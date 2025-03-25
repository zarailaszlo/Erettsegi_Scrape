import time
import os
import shutil
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Beállítások
download_path = "./downloads"
os.makedirs(download_path, exist_ok=True)
options = webdriver.ChromeOptions()
options.add_experimental_option('prefs', {
    "download.default_directory": os.path.abspath(download_path),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

subject_map = {
    '9': 'angol_nyelv',
    '4': 'tortenelem',
    '3': 'matematika',
    '1': 'magyar_nyelv_es_irodalom'
}

level_map = {'E': 'emelt', 'K': 'kozep'}

session_map = {'_1': 'majus_junius', '_2': 'oktober_november'}

# WebDriver inicializálása
driver = webdriver.Chrome(options=options)

# Linkek betöltése
with open("link.txt", "r") as file:
    urls = [line.strip() for line in file if line.strip()]

for url in urls:
    driver.get(url)

    # Paraméterek kiszedése az URL-ből
    params = re.search(r'stat=_(\d{4})_(\d)&.*eta_id=(\d+)&etj_szint=([EK])', url)
    if params:
        year, session_num, eta_id, etj_szint = params.groups()
        session_key = f'_{session_num}'
        subject = subject_map.get(eta_id, 'ismeretlen_tantargy')
        level = level_map.get(etj_szint, 'ismeretlen_szint')
        session_period = session_map.get(session_key, 'ismeretlen_idoszak')

        filename = f"{subject}_{level}_{year}_{session_period}.csv"

        # CSV letöltés gomb megtalálása
        csv_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'csv letöltése') and contains(@onclick, 'publicstat_download_kh.php')]"))
        )
        time.sleep(15)
        # CSV letöltésének elindítása
        ActionChains(driver).move_to_element(csv_button).click(csv_button).perform()

        # Várakozás, amíg a fájl letöltése befejeződik (pl. 10 másodperc)
        time.sleep(10)

        # Letöltött fájl átnevezése
        downloaded_files = os.listdir(download_path)
        downloaded_files = [f for f in downloaded_files if f.endswith(".csv")]
        downloaded_files.sort(key=lambda x: os.path.getmtime(os.path.join(download_path, x)), reverse=True)

        if downloaded_files:
            latest_file = downloaded_files[0]
            shutil.move(os.path.join(download_path, latest_file), os.path.join(download_path, filename))

# Böngésző bezárása
driver.quit()
