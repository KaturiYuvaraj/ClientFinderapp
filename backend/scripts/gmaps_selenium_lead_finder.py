import os
import time
import random
import csv
import re
import argparse
from urllib.parse import quote_plus
from typing import Optional, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    InvalidSessionIdException,
    StaleElementReferenceException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "ap_telangana_pune_delhi_mumbai_travel_tourism_leads_output.csv")

# ── SETUP CHROME DRIVER ──────────────────────────────
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Path fallback for Chrome on Windows
for chrome_path in [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
]:
    if os.path.exists(chrome_path):
        options.binary_location = chrome_path
        break

driver = None
wait = None


def create_driver():
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def init_driver():
    global driver, wait

    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass

    driver = create_driver()
    wait = WebDriverWait(driver, 20)

    driver.get("https://www.google.com/maps?hl=en")
    time.sleep(3)

    try:
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button//span[contains(text(),"Accept")]')
        )).click()
    except Exception:
        pass


# ── CONFIG ────────────────────────────────────────────
MAX_LEADS = 200

LOCATIONS = [
    ("Vijayawada", "Andhra Pradesh"),
    ("Visakhapatnam", "Andhra Pradesh"),
    ("Guntur", "Andhra Pradesh"),
    ("Tirupati", "Andhra Pradesh"),
    ("Hyderabad", "Telangana"),
    ("Warangal", "Telangana"),
    ("Pune", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Mumbai", "Maharashtra")
]

BASE_QUERIES = [
    "travel agency",
    "tour operator",
    "travel and tourism company",
    "holiday package agency",
    "domestic tour operator",
    "international tour operator",
    "travel consultant",
    "adventure tour operator",
    "pilgrimage tour operator",
    "travel services company",
    "vacation planner",
    "cruise travel agency"
]

CSV_COLUMNS = [
    "Name", "Phone", "Email", "Website", "City", "State",
    "Has Website", "Reviews", "Score", "Pitch"
]

REJECT_PATTERNS = ["/photo", "/review", "/contrib", "ludocid", "@0,", "can't reach the internet"]


# ── HELPERS ───────────────────────────────────────────
def restart_driver():
    global driver, wait
    print("⚠️ Restarting browser due to invalid session...")
    try:
        driver.quit()
    except Exception:
        pass
    init_driver()


def search_query(query):
    search_url = f"https://www.google.com/maps/search/{quote_plus(query)}?hl=en"
    print(f"🌐 Searching: {query}")

    try:
        driver.get(search_url)
    except InvalidSessionIdException:
        restart_driver()
        return False
    except WebDriverException as e:
        if "invalid session id" in str(e).lower():
            restart_driver()
            return False
        raise

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
    except Exception:
        print("⚠️ Search results feed not found quickly; continuing anyway")

    time.sleep(random.uniform(3, 5))
    return True


def scroll_results():
    try:
        div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        for _ in range(8):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", div)
            time.sleep(random.uniform(1.5, 2.5))
    except InvalidSessionIdException:
        restart_driver()
    except Exception:
        pass


def collect_urls():
    try:
        links = driver.find_elements(By.XPATH, '//a[contains(@href,"/maps/place/")]')
    except InvalidSessionIdException:
        restart_driver()
        return []
    except WebDriverException as e:
        if "invalid session id" in str(e).lower():
            restart_driver()
            return []
        return []

    seen, urls = set(), []

    for a in links:
        try:
            href = a.get_dom_attribute("href")
        except StaleElementReferenceException:
            continue

        if not href or any(x in href for x in REJECT_PATTERNS):
            continue

        base = re.match(r"(https://www\.google\.com/maps/place/[^/]+/)", href)
        key = base.group(1) if base else href

        if key not in seen:
            seen.add(key)
            urls.append(href)

    return urls


def safe_text(xpath):
    try:
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        text = element.text.strip()
        return text if text else "N/A"
    except InvalidSessionIdException:
        restart_driver()
        return "N/A"
    except WebDriverException as e:
        if "invalid session id" in str(e).lower():
            restart_driver()
        return "N/A"
    except Exception:
        return "N/A"


def safe_attr(xpath, attr):
    try:
        return wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute(attr) or "N/A"
    except InvalidSessionIdException:
        restart_driver()
        return "N/A"
    except WebDriverException as e:
        if "invalid session id" in str(e).lower():
            restart_driver()
        return "N/A"
    except Exception:
        return "N/A"


def get_reviews(text):
    match = re.search(r"([\d,]+)", text)
    return int(match.group(1).replace(",", "")) if match else 0


def get_listing_name():
    xpaths = [
        '//h1',
        '//h1//span',
        '//div[@role="heading"]//span',
        '//div[@id="pane"]//h1',
        '//button[@data-item-id="title"]/div',
        '//span[contains(@class,"font")]/span'
    ]

    for xpath in xpaths:
        name = safe_text(xpath)
        if name != "N/A" and len(name) > 1 and not name.lower().startswith("search"):
            return name

    title = driver.title or ""
    if " - Google Maps" in title:
        title_name = title.replace(" - Google Maps", "").strip()
        if title_name and title_name.lower() != "google maps":
            return title_name

    if title and title.lower() != "google maps":
        return title.strip()

    return "N/A"


def safe_driver_get(url, retry=True):
    try:
        driver.get(url)
        return True
    except InvalidSessionIdException:
        restart_driver()
        if retry:
            return safe_driver_get(url, retry=False)
        return False
    except WebDriverException as e:
        if "invalid session id" in str(e).lower():
            restart_driver()
            if retry:
                return safe_driver_get(url, retry=False)
            return False
        return False
    except Exception:
        return False


def extract_email(url):
    if not url or url == "N/A":
        return "N/A"

    if not safe_driver_get(url):
        return "N/A"

    try:
        time.sleep(2)
        html = driver.page_source
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", html)
        return emails[0] if emails else "N/A"
    except InvalidSessionIdException:
        restart_driver()
        return "N/A"
    except WebDriverException as e:
        if "invalid session id" in str(e).lower():
            restart_driver()
        return "N/A"
    except Exception:
        return "N/A"


def probe_brand_domain_sync(name: str, city: str) -> Optional[str]:
    """
    Rigorously detects hidden websites like bawarchionline.com or brand.in.
    Prevents false positives where a business does have a website, but GMB omits it.
    """
    import urllib.request
    clean = re.sub(r"[^a-z0-9\s]", " ", name.lower()).strip()
    words = [w for w in clean.split() if len(w) >= 3 and w not in ("restaurant", "hotel", "agency", "services", "tours", "travel")]
    if not words:
        words = [w for w in clean.split() if len(w) >= 3]
    if not words:
        return None

    slug = words[0]
    full_slug = "".join(words[:2])

    test_urls = [
        f"https://www.{slug}.com",
        f"https://{slug}.in",
        f"https://www.{slug}.in",
        f"https://{slug}online.com",
        f"https://{slug}online.in",
        f"https://{full_slug}.com",
        f"https://{full_slug}.in",
        f"https://{full_slug}online.com",
    ]

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for u in test_urls:
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    body = resp.read(60000).decode("utf-8", errors="ignore").lower()
                    if slug in body and (city.lower() in body or any(k in body for k in ("travel", "food", "hotel", "tour", "book", "order"))):
                        return u
        except Exception:
            pass

    return None


def score_lead(has_website, reviews, name, category="travel"):
    score = 0
    score += 70 if has_website == "No" else 15

    if reviews < 10:
        score += 35
    elif reviews < 40:
        score += 20
    else:
        score += 10

    keywords = [
        "travel", "tour", "tourism", "holiday", "vacation",
        "pilgrimage", "adventure", "cruise", "travel agency",
        "restaurant", "cafe", "hotel", "salon", "clinic", "gym"
    ]
    if any(k in name.lower() for k in keywords):
        score += 30

    return min(100, score)


def generate_pitch(has_website, reviews, name, category="travel"):
    cat = category.lower()
    if has_website == "No":
        if "travel" in cat or "tour" in cat:
            return "No website — a travel website can showcase tour packages, destinations, itineraries, and booking options."
        elif "restaurant" in cat or "cafe" in cat or "food" in cat:
            return "No website — an online ordering website showcases menus, opening hours, customer reviews, and direct table/food bookings."
        elif "salon" in cat or "spa" in cat:
            return "No website — an appointment booking website allows clients to view service packages, stylists, and book slots 24/7."
        elif "clinic" in cat or "hospital" in cat:
            return "No official website — a professional clinic website displays doctor profiles, treatments, timings, and patient appointment requests."
        else:
            return f"No website — a dedicated {category} website builds customer trust, displays service offerings, and captures direct inquiries."

    if reviews < 20:
        return "Low reviews — destination guides, clear itineraries, and traveler testimonials can strengthen this travel business's online presence."

    return "Potential fit for stronger visibility around tour packages, destination experiences, and convenient travel bookings."


def main():
    parser = argparse.ArgumentParser(description="Google Maps Client Finder for Undigitalized Businesses")
    parser.add_argument("--max-leads", type=int, default=MAX_LEADS, help="Maximum leads to collect")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_FILE, help="Output CSV path")
    parser.add_argument("--category", type=str, default="travel", help="Category filter")
    args = parser.parse_args()

    max_leads = args.max_leads
    output_file = args.output
    category = args.category

    init_driver()
    all_urls, seen = [], set()

    for base in BASE_QUERIES:
        for city, state in LOCATIONS:
            query = f"{base} {city} {state} India"
            print(f"\n🔍 {query}")

            if not search_query(query):
                print("❌ Search failed, skipping query")
                continue

            scroll_results()

            urls = collect_urls()
            print(f"➡️ Found {len(urls)} URLs for '{query}'")

            for url in urls:
                if url not in seen:
                    seen.add(url)
                    all_urls.append((url, city, state))

            print(f"   cumulative URLs: {len(all_urls)}")
            time.sleep(random.uniform(2, 4))

    print(f"\n🔗 Total unique URLs collected: {len(all_urls)}")

    data = []

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        f.flush()
        os.fsync(f.fileno())

    for url, city, state in all_urls:
        if len(data) >= max_leads:
            break

        try:
            if not safe_driver_get(url):
                print("Warning: Could not load listing page, skipping:", url)
                continue

            time.sleep(random.uniform(2.5, 4))

            name = get_listing_name()
            if name == "N/A":
                print("Warning: Skipping listing with no name:", url)
                continue

            phone = safe_attr('//button[contains(@data-item-id,"phone")]', 'aria-label')
            phone = re.sub(r"[^\d+]", "", phone)

            website = safe_attr('//a[contains(@data-item-id,"authority")]', 'href')

            # Anti-false-positive check: verify brand domain probe (e.g. bawarchionline.com)
            if website == "N/A":
                probed_web = probe_brand_domain_sync(name, city)
                if probed_web:
                    website = probed_web

            has_website = "Yes" if website != "N/A" else "No"

            rating_text = safe_attr('//span[@role="img"]', 'aria-label')
            reviews = get_reviews(rating_text)

            email = "N/A"
            if has_website == "Yes":
                email = extract_email(website)

            score = score_lead(has_website, reviews, name, category)
            pitch = generate_pitch(has_website, reviews, name, category)

            print(f"Scraped: {name} | Score: {score} | Website: {has_website}")

            row = [name, phone, email, website, city, state, has_website, reviews, score, pitch]
            data.append(row)

            with open(output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)

        except InvalidSessionIdException:
            print("Warning: invalid session id during detail scraping, restarting browser and skipping URL:", url)
            restart_driver()
        except WebDriverException as e:
            if "invalid session id" in str(e).lower():
                print("Warning: invalid session id during detail scraping, restarting browser and skipping URL:", url)
                restart_driver()
            else:
                print("Error scraping listing details:", e)
        except Exception as e:
            print("Error scraping listing details:", e)

    # Sort: Put businesses without any website first, ranked by highest score
    data.sort(key=lambda row: (row[6] == "Yes", -row[8]))

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(data)

    print(f"\nDONE — {len(data)} leads saved to {output_file}")
    driver.quit()


if __name__ == "__main__":
    main()
