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

# === CONFIGURATION ===
TOKEN = '7558549874:AAHvAyPxkV10uKwotOOzMgVBpufx-jmFwtE'  # Ton token Telegram
CHAT_ID = '1035855865'                                    # Ton chat ID Telegram

APOGEE = '24010503'              # Numéro Apogée
BIRTHDATE = '31/08/1995'         # Date de naissance au format jj/mm/aaaa

LOGIN_URL = 'https://fsjp.uh1.ac.ma/scolarite/login.php'
CHROMEDRIVER_PATH = '/usr/bin/chromedriver'

chrome_options = Options()
chrome_options.add_argument("--headless")  # Supprime cette ligne si tu veux voir le navigateur

# === VARIABLES GLOBALES ===
last_table_hash = None

def send_telegram_message(message):
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

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 1. Aller sur la page de login
        driver.get(LOGIN_URL)

        # 2. Remplir les identifiants
        driver.find_element(By.ID, 'apogee').send_keys(APOGEE)
        driver.find_element(By.ID, 'birthdate').send_keys(BIRTHDATE)
        driver.find_element(By.TAG_NAME, 'form').submit()

        # 3. Attendre redirection vers dashboard.php
        WebDriverWait(driver, 10).until(EC.url_contains('dashboard.php'))
        if "dashboard.php" not in driver.current_url:
            raise Exception("Échec de la connexion. Vérifie les identifiants.")

        # 4. Cliquer sur "Session de printemps"
        bouton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'btnRatt')))
        bouton.click()

        # 5. Attendre chargement du tableau
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped.table-bordered.mt-3 tbody tr'))
        )

        # 6. Calcul du hash du tableau
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
