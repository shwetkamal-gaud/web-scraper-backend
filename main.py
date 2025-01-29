
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from bs4 import BeautifulSoup

import undetected_chromedriver as uc

def start_undetected_chrome():
    """Starts an undetected Chrome browser with anti-detection settings"""
    options = uc.ChromeOptions()

    
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options, use_subprocess=True)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver



def get_product_id(company_name):
    search = f'https://www.capterra.com/search/?query={company_name}'
    driver = start_undetected_chrome()
    try:
        driver.get(search)
        time.sleep(6)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        first_result = soup.find("a", {"data-testid": "star-rating"})

        if first_result:
            product_url = first_result["href"]
            
            return product_url

        return None
    finally:
        driver.quit()


def scrape_reviews(company_name, start_date, end_date, source):
    company_slug = company_name.lower().replace(" ", "-")
    source_slug  = source.lower()
    if source_slug == 'g2':
        url = f"https://www.{source_slug}.com/products/{company_slug}/reviews"
    elif source_slug == 'capterra':
        product_url = get_product_id(company_name)
        if not product_url:
            print(f'could not find Capterra product url for {company_name}.')
            return []
        url = product_url
    else:
        print("Invalid source! Choose either 'G2' or 'Capterra'.")
        return[]


    driver = start_undetected_chrome()
    try:
        driver.get(url)
        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        reviews =  []
        if(source_slug == "g2"):
            for review in soup.find_all("div", class_='f-1'):
                title = review.find("a", class_='pjax').text.strip()
                description  = review.find("p", class_='formatted-text').text.strip()
                date_text = review.find("span > time", class_="x-current-review-date").text.strip()

                review_date = datetime.strptime(date_text, "%Y-%m-%d")
                if start_date <= review_date <= end_date:
                    reviews.append({
                        "title": title,
                        "description": description,
                        "date": date_text
                    })
        elif(source_slug =="capterra"):
            for review in soup.find_all("div[data-test-id='review-card']"):
                title = review.find("p", class_="font-bold").text.strip()
                description = [review.find("p[data-testid='pros-content']").text.strip(), review.find("p[data-testid='cons-content']").text.strip() ]
                date_text = review.find("div", class_="my-3xs flex items-center").text.strip()

                review_date = datetime.strptime(date_text, "%Y-%m-%d")
                if start_date <= review_date <= end_date:
                    reviews.append({
                        "title": title,
                        "description": description,
                        "date": date_text
                    })
        return reviews

    
    except Exception as error:
        print(f'Error While Scrapping {source}: {str(error)}')
        return[]
    finally:
        if driver:
            driver.quit()

def save_to_json(reviews, output_file):
    with open(output_file, "w") as file:
        json.dump(reviews, file, indent=4)

if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    start_date = datetime.strptime(input("Enter the start date (YYYY-MM-DD): "), "%Y-%m-%d")
    end_date = datetime.strptime(input("Enter the end date (YYYY-MM-DD): "), "%Y-%m-%d")
    source = input("Enter the source (G2/Capterra): ")

    reviews = scrape_reviews(company_name, start_date, end_date, source)
    save_to_json(reviews, "reviews.json")