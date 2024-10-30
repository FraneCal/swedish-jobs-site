from bs4 import BeautifulSoup
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://jobb.blocket.se/lediga-jobb?filters=stockholms-laen"
header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
}

total_pages = 500  # Total number of pages to scrape
max_retries = 5    # Maximum number of retries for each page
all_links = []     # List to store all job links

# Function to scrape a single page
def scrape_page(page_num):
    url = f"{BASE_URL}?page={page_num}"
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=header)
            response.raise_for_status()  # Check for request errors

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all("a", class_="sc-bc48e3a4-0")
            page_links = [
                f'https://jobb.blocket.se{link.get("href")}' 
                for link in links 
                if not link.get("href").endswith("/sortering")
            ]
            
            print(f"Page {page_num} scraped, {len(page_links)} links found.")
            return page_links  # Return links found on this page

        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError) as e:
            retries += 1
            print(f"Error on page {page_num}, retrying {retries}/{max_retries}...")
            time.sleep(2)  # Short delay before retrying
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve page {page_num}. Error: {e}")
            return []  # Return empty list if request fails

# Main scraping logic with concurrency
start_time = time.time()
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(scrape_page, page) for page in range(1, total_pages + 1)]
    
    for future in as_completed(futures):
        page_links = future.result()
        if page_links:
            all_links.extend(page_links)  # Collect all links from each page

# Write all links to the file once at the end
with open("4_4.txt", "w") as file:
    for link in all_links:
        file.write(link + "\n")

print(f"Scraping complete. {len(all_links)} links saved to job_links_2.txt.")
print(f"Total time taken: {time.time() - start_time:.2f} seconds.")
