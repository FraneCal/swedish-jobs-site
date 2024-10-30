import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import base64
from io import BytesIO

# Function to extract job details, including any logo image
def extract_job_details(url, retries=3):
    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    }

    while retries > 0:
        try:
            response = requests.get(url, headers=header, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract basic job details
            company = soup.find("a", class_="sc-5fe98a8b-2 iapiPt")
            job_title = soup.find("h1", class_="sc-5fe98a8b-7 bdVXli")
            area_of_work = soup.find("a", class_="sc-dd9f06d6-6 gTlWWR")
            date_posted = soup.find("div", class_="sc-dd9f06d6-2 dVNNPW")
            last_day_to_apply = soup.find("div", class_="sc-dd9f06d6-4 kwCfOU")

            # Find any logo image by looking for <img> tags with 'logotyp' in the alt attribute
            logo_image_tag = soup.find("img", alt=re.compile("logotyp", re.IGNORECASE))
            if logo_image_tag:
                image_url = logo_image_tag['src']
                # Download and encode image in base64
                image_data = requests.get(image_url).content
                encoded_image = base64.b64encode(image_data).decode("utf-8")
                image_data_uri = f"data:image/jpeg;base64,{encoded_image}"
                
                # Decode and save the image to file
                decoded_image_data = base64.b64decode(encoded_image)
                output_image_path = f"images/{job_title.getText().replace(' ', '_')}_logo.jpg"
                with open(output_image_path, "wb") as image_file:
                    image_file.write(decoded_image_data)
                print(f"Logo image saved as {output_image_path}")
            else:
                image_data_uri = "No image"

            # Prepare job details data
            data = {
                "Image": image_data_uri,  # Encoded image in the first column
                "Company": company.getText() if company else "N/A",
                "Job Title": job_title.getText() if job_title else "N/A",
                "Area of Work": area_of_work.getText() if area_of_work else "N/A",
                "Date Posted": date_posted.getText() if date_posted else "N/A",
                "Last Day to Apply": last_day_to_apply.getText() if last_day_to_apply else "N/A",
                "Emails": extract_emails(response.text),
                "Phones": extract_phones(soup)
            }
            return data  # Return data if successful

        except requests.exceptions.RequestException as e:
            print(f"Error processing {url}: {e}")
            retries -= 1
            time.sleep(2)  # Small delay before retrying

    return None  # Return None if all retries fail

def extract_emails(text):
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = set(re.findall(email_pattern, text))
    return ", ".join(emails) if emails else "/"

def extract_phones(soup):
    box = soup.find("div", class_="sc-d56e3ac2-5")
    if box:
        phone_pattern = r"(07\d{1,3}[- ]\d{1,8}|\b03\d{1,3}[- ]\d{1,8})"
        phones = set(re.findall(phone_pattern, box.getText()))
        return ", ".join(phones) if phones else "/"
    return "/"

# Read links and initialize lists
with open("job_links.txt", "r") as file:
    links = [line.strip() for line in file if line.strip()]

job_listings = []
failed_links = []

# Process each link
for idx, link in enumerate(links):
    print(f"Processing {idx + 1}/{len(links)}: {link}")
    job_details = extract_job_details(link)

    if job_details:
        job_listings.append(job_details)
        print(f"Successfully processed: {job_details['Job Title']} at {job_details['Company']}.")
    else:
        print(f"Failed to process: {link}")
        failed_links.append(link)

# Convert job details to a DataFrame
df = pd.DataFrame(job_listings)

# Save DataFrame to Excel
file_name = "jobs_with_images.xlsx"
with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Job Listings")

print(f"Data saved to {file_name}.")
print(f"{len(failed_links)} links could not be processed and were saved to 'failed_links.txt'.")

# Save failed links to a separate file
if failed_links:
    with open("jobs failed links.txt", "w") as failed_file:
        failed_file.write("\n".join(failed_links))
