import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from app.config import settings
from app.database.models import Base

logger = logging.getLogger("client_finder.database")

def create_db_engine():
    db_url = settings.DATABASE_URL
    is_mysql = "mysql" in db_url.lower()

    if is_mysql:
        try:
            eng = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to MySQL database: client_finder")
            return eng
        except Exception as e:
            if settings.DATABASE_FALLBACK_SQLITE:
                logger.info("MySQL connection not yet configured with valid credentials.")
                logger.info("Falling back seamlessly to local SQLite database (client_finder_dev.db) for development.")
                logger.info("Tip: To use MySQL, set your root password in backend/.env: DATABASE_URL=mysql+pymysql://root:<password>@localhost:3306/client_finder")
                sqlite_path = Path(__file__).resolve().parent.parent.parent / "client_finder_dev.db"
                sqlite_url = f"sqlite:///{sqlite_path}"
                return create_engine(
                    sqlite_url,
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            else:
                logger.error(f"Failed to connect to MySQL: {e}")
                raise e
    else:
        # SQLite or other DB
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url.lower() else {},
            echo=False
        )

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create tables if they do not exist"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema synchronized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise e

def get_db():
    """FastAPI database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
