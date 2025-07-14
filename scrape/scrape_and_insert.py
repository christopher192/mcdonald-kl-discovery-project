import os
import time
import json
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PGHOST = os.getenv("PGHOST", "db")
PGPORT = os.getenv("PGPORT", "5432")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "admin")
PGDATABASE = os.getenv("PGDATABASE", "postgis")

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

url = 'https://www.mcdonalds.com.my/locate-us'

conn = psycopg2.connect(
    dbname=PGDATABASE,
    user=PGUSER,
    password=PGPASSWORD,
    host=PGHOST,
    port=PGPORT
)
cursor = conn.cursor()

driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

wait = WebDriverWait(driver, 15)

states_dropdown_elem = wait.until(EC.presence_of_element_located((By.ID, "states")))
dropdown = Select(states_dropdown_elem)
dropdown.select_by_visible_text("Kuala Lumpur")

categories_dropdown_elem = wait.until(EC.presence_of_element_located((By.ID, "categories")))
categories_dropdown = Select(categories_dropdown_elem)
categories_dropdown.select_by_visible_text("All Categories")

time.sleep(5)

soup = BeautifulSoup(driver.page_source, 'html.parser')
divs = soup.find_all("div", class_="columns large-3 medium-4 small-12")
print("total items found:", len(divs))

for div in divs:
    script_tag = div.find("script", type="application/ld+json")
    if script_tag:
        data = json.loads(script_tag.string)
        name = data.get("name")
        address = data.get("address")
        telephone = data.get("telephone")
        latitude = data.get("geo", {}).get("latitude")
        longitude = data.get("geo", {}).get("longitude")

        categories = []
        for a in div.select(".addressTop a .ed-tooltiptext"):
            category = a.get_text(strip=True)
            categories.append(category)
        categories_str = ', '.join(categories)

        print(f"{name}, {address}, {telephone}, {latitude}, {longitude}")
        print("Categories:", categories_str)

        cursor.execute('''
            INSERT INTO mcdonald (name, address, telephone, latitude, longitude, categories, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY)
        ''', (name, address, telephone, latitude, longitude, categories_str, float(longitude), float(latitude)))
        conn.commit()
        print(f"Inserted: {name}")

print("All data inserted into database successfully.")

driver.quit()
conn.close()