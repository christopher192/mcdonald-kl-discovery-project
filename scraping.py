#!/usr/bin/env python
# coding: utf-8

# ## Web Scraping & Data Population

# In[7]:


import time
import json
import psycopg2
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# #### Implementation Code for Web Scraping & Data Handling

# In[8]:


url = 'https://www.mcdonalds.com.my/locate-us'

# connect to PostgreSQL with PostGIS enabled
conn = psycopg2.connect(
    dbname='postgis',
    user='postgres',
    password='admin',
    host='localhost',
    port='5432'
)
cursor = conn.cursor()

driver = webdriver.Chrome()
driver.get(url)

# setup WebDriverWait for waiting
wait = WebDriverWait(driver, 10)

# wait and select 'Kuala Lumpur'
states_dropdown_elem = wait.until(EC.presence_of_element_located((By.ID, "states")))
dropdown = Select(states_dropdown_elem)
dropdown.select_by_visible_text("Kuala Lumpur")
# alternatively, select by value
# dropdown.select_by_value("Kuala Lumpur")

# wait and select 'All Categories'
categories_dropdown_elem = wait.until(EC.presence_of_element_located((By.ID, "categories")))
categories_dropdown = Select(categories_dropdown_elem)
categories_dropdown.select_by_visible_text("All Categories")

# skip the "Search" button as the page updates automatically when the dropdowns are selected
# wait for 5 seconds after selecting the dropdowns
time.sleep(5)

# begin scraping
soup = BeautifulSoup(driver.page_source, 'html.parser')

# find all restaurants
divs = soup.find_all("div", class_="columns large-3 medium-4 small-12")

print("total items found:", len(divs))

for div in divs:
    # get json data from <script> tag
    script_tag = div.find("script", type="application/ld+json")
    if script_tag:
        data = json.loads(script_tag.string)
        name = data.get("name")
        address = data.get("address")
        telephone = data.get("telephone")
        latitude = data.get("geo", {}).get("latitude")
        longitude = data.get("geo", {}).get("longitude")
    
    # get the categories
    categories = []
    for a in div.select(".addressTop a .ed-tooltiptext"):
        category = a.get_text(strip=True)
        categories.append(category)

    categories_str = ', '.join(categories)

    # print for verification
    print(f"{name}, {address}, {telephone}, {latitude}, {longitude}")
    print("Categories:", categories_str)
    print("-----")

    # insert into PostgreSQL with geom point
    cursor.execute('''
        INSERT INTO mcdonald (name, address, telephone, latitude, longitude, categories, geom)
        VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::GEOGRAPHY)
    ''', (name, address, telephone, latitude, longitude, categories_str, float(longitude), float(latitude)))
    conn.commit()

    print(f"inserted data: {name}, {address}, {telephone}, {latitude}, {longitude}, {categories_str}")

print("all data inserted into database successfully")

# close the connection
driver.quit()
conn.close()


# #### Data Verification

# In[11]:


# connect to PostgreSQL database with PostGIS enabled
conn = psycopg2.connect(
    dbname='postgis',
    user='postgres',
    password='admin',
    host='localhost',
    port='5432'
)
cursor = conn.cursor()

# execute SELECT * query
cursor.execute("SELECT id, name, address, telephone, latitude, longitude, categories FROM mcdonald")

# fetch all rows
rows = cursor.fetchall()

# print each row
for row in rows:
    print(row)

# close the connection
conn.close()


# #### Select intersecting outlet within 5 km using PostGIS

# In[ ]:


# connect to PostgreSQL database with PostGIS enabled
conn = psycopg2.connect(
    dbname='postgis',
    user='postgres',
    password='admin',
    host='localhost',
    port='5432'
)
cursor = conn.cursor()

# execute query to find intersecting outlets within 5 km radius
cursor.execute("""
    SELECT a.id AS outlet_a_id, a.name AS outlet_a_name,
           b.id AS outlet_b_id, b.name AS outlet_b_name
    FROM mcdonald a
    JOIN mcdonald b
      ON a.id != b.id
     AND ST_DWithin(a.geom, b.geom, 5000);
""")

# fetch all rows
rows = cursor.fetchall()

# print each intersecting pair
for row in rows:
    print(f"Outlet A ID: {row[0]}, Name: {row[1]} | Outlet B ID: {row[2]}, Name: {row[3]}")

# close the connection
conn.close()


# In[ ]:




