from pyvirtualdisplay import Display
display = Display(visible=0, size=(1024, 768))
display.start()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import hashlib
import os

# === CONFIGURATION via variables d'environnement ===
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
APOGEE = os.getenv('APOGEE')
BIRTHDATE = os.getenv('BIRTHDATE')

LOGIN_URL = 'https://fsjp.uh1.ac.ma/scolarite/login.php'
CHROMEDRIVER_PATH = '/usr/bin/chromedriver'

chrome_options = Options()
chrome_options.binary_location = '/usr/bin/chromium'  # Important pour Docker
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

last_table_hash = None

def send_telegram_message(message):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Token Telegram ou Chat ID non défini.")
        return
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Erreur Telegram : {response.text}")

def get_table_hash(driver):
    lignes = driver.find_elements(By.CSS_SELECTOR, 'table.table-striped.table-bordered.mt-3 tbody tr')
    textes = [ligne.text for ligne in lignes]
    contenu = "".join(textes)
    return hashlib.md5(contenu.encode()).hexdigest(), len(lignes)

def check_table():
    global last_table_hash

    if not APOGEE or not BIRTHDATE:
        print("⚠️ Numéro Apogée ou Date de naissance non défini.")
        return

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(LOGIN_URL)

        driver.find_element(By.ID, 'apogee').send_keys(APOGEE)
        driver.find_element(By.ID, 'birthdate').send_keys(BIRTHDATE)
        driver.find_element(By.TAG_NAME, 'form').submit()

        WebDriverWait(driver, 10).until(EC.url_contains('dashboard.php'))
        if "dashboard.php" not in driver.current_url:
            raise Exception("Échec de la connexion. Vérifie les identifiants.")

        bouton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'btnRatt')))
        bouton.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped.table-bordered.mt-3 tbody tr'))
        )

        current_hash, current_count = get_table_hash(driver)
        print(f"✅ Résultats détectés : {current_count} ligne(s)")

        if last_table_hash is None:
            last_table_hash = current_hash
            print("📦 Premier lancement, état initial mémorisé.")
        elif current_hash != last_table_hash:
            send_telegram_message(f"🎉 Nouveaux résultats détectés ! Total : {current_count} lignes.")
            last_table_hash = current_hash
        else:
            print("🕓 Aucun changement détecté.")

    except Exception as e:
        msg = f"❌ Erreur : {e}"
        print(msg)
        send_telegram_message(msg)

    finally:
        driver.quit()

if __name__ == '__main__':
    while True:
        check_table()
        time.sleep(300)  # Pause de 5 minutes
