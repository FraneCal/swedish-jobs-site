from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Set up the Selenium WebDriver (e.g., Chrome)
driver = webdriver.Chrome()  # Adjust if using a different browser
driver.maximize_window()

BASE_URL = "https://jobb.blocket.se/lediga-jobb?filters=blekinge-laen&filters=dalarnas-laen&filters=gotlands-laen&filters=gaevleborgs-laen&filters=hallands-laen&filters=jaemtlands-laen&filters=joenkoepings-laen&filters=kalmar-laen&filters=kronobergs-laen&filters=norrbottens-laen"
total_pages = 500  # Total number of pages to scrape
all_links = []  # List to store all job links

def scrape_page():
    # Wait for job links to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "sc-bc48e3a4-0"))
    )

    # Scroll to the bottom of the page to load all dynamic content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Pause briefly to allow additional content to load

    # Collect job links from the current page
    links = driver.find_elements(By.CLASS_NAME, "sc-bc48e3a4-0")
    page_links = [
        f'https://jobb.blocket.se{link.get_attribute("href")}'
        for link in links
        if link.get_attribute("href") and not link.get_attribute("href").endswith("/sortering")
    ]

    print(f"{len(page_links)} links found on the page.")
    return page_links

# Open the base URL
driver.get(BASE_URL)

for page_num in range(1, total_pages + 1):
    print(f"Processing page {page_num}...")
    
    # Scrape the current page
    page_links = scrape_page()
    all_links.extend(page_links)

    # Find and click the "Next" button using its XPath
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[rel="next nofollow"]'))
        )
        ActionChains(driver).move_to_element(next_button).click(next_button).perform()
        time.sleep(2)  # Wait briefly after clicking to allow page to load
    except Exception as e:
        print(f"No 'Next' button found or couldn't click. Ending on page {page_num}. Error: {e}")
        break  # Exit the loop if there's no "Next" button

# Close the WebDriver
driver.quit()

# Save all links to a file
with open("links by location/5_5.txt", "w") as file:
    for link in all_links:
        file.write(link + "\n")

print(f"Scraping complete. {len(all_links)} links saved.")