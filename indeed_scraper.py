from bs4 import BeautifulSoup
import requests
import csv
from time import sleep
from random import randint
from datetime import datetime
from lxml.html import fromstring
from itertools import cycle
import traceback

# Author: Diego Portela
# Webscrapper program for indeed.com.au
# This program was developed for education purposes only!
# THE CODE SHARED IN THIS REPOSITORY SHOULD NEVER BE USED OR EXPLOITED
# Note: Headers are not used in this program but can be implemented
# If there is difficulties connecting to Indeed.com.au

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.47'
}

def get_record(card, new_proxy):
    href = card.get('href')
    new_url = 'https://indeed.com.au' + href

    # To avoid being kicked for frequent requests
    #delay = randint(1, 2)
    #sleep(delay)
    
    response_desc = requests.get(new_url,proxies={"http": ("http://"+new_proxy), "https": ("http://"+new_proxy)})
    print("Description URL Status: " + str(response_desc.status_code))
    
    response_desc.encoding = response_desc
    soup_desc = BeautifulSoup(response_desc.text, 'html.parser')
    
    card_description_soup = soup_desc.find('div', {"class":"jobsearch-jobDescriptionText"})
    card_description = ''

    for child in card_description_soup.findChildren(recursive=True):
        card_description = card_description + (child.getText()) + " "
    
    real_url = response_desc.url
    
    # Go into href and collect description
    
    card_title_f = (card.find('h2', {"class": "jobTitle"}).find_all('span'))
    if (len(card_title_f) > 1):
        card_title = card_title_f[1].text.strip()
    else:
        card_title = card_title_f[0].text.strip()
    
    card_cname = (card.find("span", {"class": "companyName"}).text.strip())
    card_location = (card.find("div", {"class": "companyLocation"}).text.strip())
    card_summary = (card.find("div", {"class": "job-snippet"}).text.strip())
    card_date = card.find('span', 'date').text
    today = datetime.today().strftime("%Y-%m-%d")
    try:
        card_salary = card.find('span', {"class": "salary-snippet"}).text.strip()
    except:
        card_salary = ''
    
    record = (card_title, card_cname, card_location, card_salary, card_date, today, card_summary, card_description, real_url)

    new_url = ""

    return record

def working_proxy(url):
    proxies = get_proxies()
    proxy_pool = cycle(proxies)
    
    new_proxy = ''
    i = 0
    while True:
        #Get a proxy from the pool
        proxy = next(proxy_pool)
        i = i+1
        print("Request #%d"%i)
        try:
            print(("testing proxy - http://"+proxy))
            response = requests.get(url, timeout=5, proxies={"http": ("http://"+proxy), "https": ("http://"+proxy)})
            print("status: " + str(response.status_code()))
            print("Success!")
            new_proxy = proxy
            break
                
        except:
            #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
            #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url 
            print("Skipping. Connnection error")
    return new_proxy

def main():
    """Run the main program"""
    records = []
    values = 0
    url = 'https://www.indeed.com.au/data-jobs'
    
    # Create template for CSV file
    with open('results.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Job Title', 'Company', 'Location', 'Salary', 'Posting Date', 'Extract Date', 'Summary', 'Description', 'Job Url'])

    new_proxy = working_proxy(url)
    
    # Data Scraping
    while True:

        try:
            response = requests.get(url,proxies={"http": ("http://"+new_proxy), "https": ("http://"+new_proxy)})
            response.encoding = response
            print("New URL Status: " + str(response.status_code))
            print(response.url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all('a', 'tapItem')
    
            for card in cards:
                record = get_record(card, new_proxy)
                records.append(record)
                
        except AttributeError:
            print("Error Occurred.") 

        
        # Save the data to CSV
        with open('results.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(records) 
        
        values = values + len(records)
        print("Total Scraped: " + str(values))
        records = []
            
        try:
            url = 'https://www.indeed.com.au' + soup.find('a', {'aria-label': 'Next'}).get('href')
            #delay = randint(1, 2)
            #sleep(delay)
        except AttributeError:
            print("CAPTA OR PROXY ISSUE")
            new_proxy = working_proxy(url)
            

# Proxy hopping to avoid indeed detecting scraping
def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
        #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


main()
