-- AI Client Finder Database Schema
-- MySQL 8.0+ Compatible

CREATE DATABASE IF NOT EXISTS client_finder CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE client_finder;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Leads Table
CREATE TABLE IF NOT EXISTS leads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    provider_id VARCHAR(255) NULL,
    business_name VARCHAR(255) NOT NULL,
    category VARCHAR(255) NULL,
    phone VARCHAR(100) NULL,
    website VARCHAR(500) NULL,
    address TEXT NULL,
    city VARCHAR(255) NULL,
    latitude DECIMAL(10, 7) NULL,
    longitude DECIMAL(10, 7) NULL,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    review_count INT DEFAULT 0,
    source VARCHAR(100) DEFAULT 'Authorized Business API',
    source_url VARCHAR(500) NULL,
    service VARCHAR(255) NOT NULL,
    lead_score INT DEFAULT 0,
    opportunity_type VARCHAR(255) NULL,
    opportunity_reason TEXT NULL,
    confidence VARCHAR(50) DEFAULT 'Moderate',
    status VARCHAR(50) DEFAULT 'New',
    notes TEXT NULL,
    follow_up_date DATE NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_leads_user_id (user_id),
    INDEX idx_leads_status (status),
    INDEX idx_leads_service (service),
    INDEX idx_leads_score (lead_score),
    INDEX idx_leads_business_name (business_name),
    INDEX idx_leads_user_provider (user_id, provider_id),
    INDEX idx_leads_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Searches Table (Search History)
CREATE TABLE IF NOT EXISTS searches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    radius VARCHAR(50) NOT NULL,
    keywords VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_searches_user_date (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Generated Messages Table
CREATE TABLE IF NOT EXISTS generated_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lead_id INT NULL,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
    INDEX idx_messages_user (user_id),
    INDEX idx_messages_lead (lead_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
