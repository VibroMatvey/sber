import os
import time
from datetime import datetime
from random import randint
import selenium.common.exceptions
from fake_useragent import UserAgent
from fastapi import HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from db import models
import pickle
import bcrypt
from sqlalchemy import desc


def create_driver(login):
    options = webdriver.ChromeOptions()
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(
        r"user-data-dir=" + os.path.abspath(f'venv/Lib/site-packages/selenium/profile/{login}')
    )
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument(f'--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=900, 900')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--headless')
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(os.path.abspath('drivers/chromedriver_win.exe')), options=options)
    return driver


class SberLogin:
    drivers = {}

    def login_account(self, account, driver, db):
        if self.drivers.get(account.login):
            self.drivers[account.login].close()
            self.drivers.pop(account.login)
        driver.get('https://online.sberbank.ru/CSAFront/index.do')
        time.sleep(1)
        try:
            login = driver.find_element(By.NAME, "login")
            login.send_keys(account.login)
            password = driver.find_element(By.NAME, "password")
            password.send_keys(account.password)
            password.submit()
        except selenium.common.exceptions.NoSuchElementException:
            password = driver.find_element(By.NAME, "password")
            password.send_keys(account.password)
            password.submit()
        try:
            time.sleep(1)
            confirm_password = driver.find_element(By.NAME, "confirmPassword")
            self.drivers[account.login] = driver
            db.query(models.Account).where(models.Account.login == account.login).update({
                "status": "СМС подтверждение"
            })
            db.commit()
        except selenium.common.exceptions.NoSuchElementException:
            db.query(models.Account).where(models.Account.login == account.login).update({
                "status": "Требуется авторизация"
            })
            db.commit()
            driver.close()

    def sms_confirm(self, account):
        if not self.drivers.get(account.login):
            return False
        driver = self.drivers[account.login]
        confirm_password = driver.find_element(By.NAME, "confirmPassword")
        confirm_password.send_keys(account.sms)
        confirm_password.submit()
        time.sleep(2)
        try:
            skip_button = driver.find_element(By.XPATH,
                                              "/html/body/div[3]/div/main/section/div[2]/div[1]/div[2]/div[2]/div/button")
            skip_button.click()
            time.sleep(2)
        except selenium.common.exceptions.NoSuchElementException:
            pass
        time.sleep(2)
        pickle.dump(driver.get_cookies(), open(f"static/cookies/{account.login}.pkl", "wb"))
        driver.close()
        self.drivers.pop(account.login)


async def get_accounts(db, user_id):
    accounts = db.query(models.Account).filter(models.Account.user_id == user_id).order_by(desc(models.Account.id)).all()
    return accounts


async def get_account(db, account_id, user_id):
    account = db.query(models.Account).where(models.Account.id == int(account_id)).filter(
        models.Account.user_id == user_id).first()
    if account:
        if account.photos:
            account.photos = account.photos.split(',')
        else:
            account.photos = []
        return account
    raise HTTPException(404, {
        "message": "account not found"
    })


def login_sber(account, db):
    driver = SberLogin()
    d = create_driver(account.login)
    driver.login_account(account, d, db)


def sms_confirmation_sber(account, db):
    driver = SberLogin()
    driver.sms_confirm(account)
    data_sber(account, db)


def data_sber(account, db):
    driver = create_driver(account.login)
    try:
        driver.get('https://web4-new.online.sberbank.ru/pfm/finances?tab=all')
        if os.path.exists(f'static/cookies/{account.login}.pkl'):
            cookies = pickle.load(open(f'static/cookies/{account.login}.pkl', "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.refresh()
        time.sleep(2)
        bill = driver.find_element(
            By.XPATH,
            "/html/body/div[1]/main/div/div[2]/div/div[5]/div/div[1]/button/div/div[2]/div[1]/p"
        )
        bill_value = bill.text.split(' ')[0]
        cards = driver.find_element(
            By.XPATH,
            '/html/body/div[1]/main/div/div[2]/div/div[5]/div/div[1]/button/div/div[2]/div[2]/div/p'
        )
        cards_value = cards.text.split(' ')[0]
        driver.get('https://web4-new.online.sberbank.ru/profile')
        time.sleep(2)
        fullname = driver.find_element(
            By.XPATH,
            '/html/body/div[1]/main/div/div[1]/div/div[2]/div/div/div/div/div[2]/h1'
        )
        fullname_value = fullname.text
        number = driver.find_element(
            By.XPATH,
            '/html/body/div[1]/main/div/div[2]/div/div/div[1]/section[2]/div/div[2]/div/div/div/div[2]/div/div/div/h5'
        )
        number_value = number.text
        address_btn = driver.find_element(
            By.XPATH,
            '/html/body/div[1]/main/div/div[2]/div/div/div[1]/section[2]/div/div[4]/div/div/div/div[1]/div/button'
        )
        address_btn.click()
        time.sleep(2)
        address = driver.find_element(
            By.XPATH,
            '/html/body/div[1]/main/div/div[2]/div/div/div[1]/section[2]/div/div[4]/div/div/div/div[2]/div[1]/div/div/h5'
        )
        address_value = address.text
        # await asyncio.to_thread(driver.get, 'https://web4-new.online.sberbank.ru/payments/limits')
        driver.get('https://web4-new.online.sberbank.ru/payments/limits')
        time.sleep(2)
        limit = driver.find_element(
            By.XPATH,
            '/html/body/div[1]/main/div/div[1]/div/div[2]/div/div/div/form/div[2]/section/div/span/input'
        )
        limit_value = limit.get_attribute('value').split(' ₽')[0]
        pickle.dump(driver.get_cookies(), open(f"static/cookies/{account.login}.pkl", "wb"))
        driver.close()
        now = datetime.now().strftime("%d.%m.%Y в %H:%M:%S")
        update_data = {
            "bill": bill_value,
            "cards_count": cards_value,
            "day_limit": limit_value,
            "fullname": fullname_value,
            "number": number_value,
            "address": address_value,
            "status": "Синхронизирован",
            "date": now
        }
        db.query(models.Account).filter(models.Account.login == account.login).update(update_data)
        db.commit()
    except selenium.common.exceptions.NoSuchElementException:
        driver.close()
        update_data = {
            "status": "Требуется авторизация",
        }
        db.query(models.Account).filter(models.Account.login == account.login).update(update_data)
        db.commit()


async def create_account(account, db):
    salt = bcrypt.gensalt(10)
    hashed_password = bcrypt.hashpw(account["password"].encode(), salt).decode('utf-8')
    db_account = models.Account(
        login=account["login"],
        password=hashed_password,
        name=account["name"],
        place=account["place"],
        code=account["code"],
        user_id=account["user_id"],
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


async def update_account_data(data, account_id, db):
    db.query(models.Account).filter(models.Account.id == account_id).update(data)
    db.commit()
    return HTTPException(200, {
        "message": "successful update"
    })


async def update_account_photo(photo, account, db):
    name_photos = []
    if account.photos:
        name_photos = account.photos.split(',')
    content = photo.file.read()
    name_photo = f"{str(randint(10000000000, 99999999999))}.{photo.filename.split('.')[-1]}"
    with open(f'static/photos/{name_photo}', 'wb') as f:
        f.write(content)
    name_photos.append(name_photo)
    name_photos = ','.join(name_photos)
    db.query(models.Account).filter(models.Account.id == account.id).update({
        "photos": name_photos
    })
    db.commit()
    return HTTPException(200, {
        "message": "successful update"
    })
