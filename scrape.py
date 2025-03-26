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
options.page_load_strategy = 'eager'  # vagy 'none'

subject_map = {
    '9': 'angol_nyelv',
    '4': 'tortenelem',
    '3': 'matematika',
    '1': 'magyar_nyelv_es_irodalom'
}
level_map = {'E': 'emelt', 'K': 'kozep'}
session_map = {'_1': 'majus_junius', '_2': 'oktober_november'}

# WebDriver indítása
driver = webdriver.Chrome(options=options, keep_alive=False)

# Linkek beolvasása
with open("link.txt", "r") as file:
    urls = [line.strip() for line in file if line.strip()]

def wait_for_new_csv(previous_files, timeout=300):
    """Vár egy új .csv fájlra a meglévő listához képest."""
    waited = 0
    while waited < timeout:
        current_files = set(f for f in os.listdir(download_path) if f.endswith(".csv"))
        new_files = current_files - previous_files
        if new_files:
            return new_files.pop()
        time.sleep(1)
        waited += 1
    return None

for url in urls:
    try:
        driver.get(url)

        params = re.search(r'stat=_(\d{4})_(\d)&.*eta_id=(\d+)&etj_szint=([EK])', url)
        if not params:
            print(f"⚠️ Nem sikerült kiolvasni paramétereket: {url}")
            continue

        year, session_num, eta_id, etj_szint = params.groups()
        subject = subject_map.get(eta_id, 'ismeretlen_tantargy')
        level = level_map.get(etj_szint, 'ismeretlen_szint')
        session = session_map.get(f"_{session_num}", 'ismeretlen_idoszak')
        filename = f"{subject}_{level}_{year}_{session}.csv"

        # Letöltés előtti fájllista
        existing_csvs = set(f for f in os.listdir(download_path) if f.endswith(".csv"))
        try:
            # Évszám alapján különböző XPATH-t használunk
            year = int(year)
            if year <= 2011:
                csv_button = WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'csv letöltése') and contains(@onclick, 'publicstat_download_regio.php')]"))
                )
            else:
                csv_button = WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'csv letöltése') and contains(@onclick, 'publicstat_download_kh.php')]"))
                )
        except Exception as e:
            print(f"❌ Nem található letöltés gomb: {url} | Hiba: {e}")
            continue

        # Letöltés indítása
        ActionChains(driver).move_to_element(csv_button).click(csv_button).perform()

        # Új fájl megvárása
        new_file = wait_for_new_csv(existing_csvs)
        if new_file:
            src_path = os.path.join(download_path, new_file)
            dst_path = os.path.join(download_path, filename)
            shutil.move(src_path, dst_path)
            print(f"✅ Letöltve és átnevezve: {filename}")
        else:
            print(f"❌ Nem sikerült letölteni: {filename} (timeout)")

    except Exception as e:
        print(f"⚠️ Hiba feldolgozás közben: {url}\n{e}")

driver.quit()
