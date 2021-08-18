from bs4 import BeautifulSoup
import requests
import csv
from time import sleep
from random import randint
from datetime import datetime
from lxml.html import fromstring
from itertools import cycle
import traceback
import concurrent.futures

# Author: Diego Portela
# Webscrapper program for indeed.com.au
# This program was developed for education purposes only!
# THE CODE SHARED IN THIS REPOSITORY SHOULD NEVER BE USED OR EXPLOITED
# Note: Headers are not used in this program but can be implemented
# If there is difficulties connecting to Indeed.com.au

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}

def get_record(card, proxy):
    href = card.get('href')
    new_url = 'https://indeed.com.au' + href

    try:
        response_desc = requests.get(new_url, headers=headers, proxies={'http' : 'http://'+proxy,'https': 'https://'+proxy})
    except requests.exceptions.RequestException as e:
            print(e)
            pass
    
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

proxy_list = []

def extract(proxy):
    #this was for when we took a list into the function, without conc futures.
    #proxy = random.choice(proxylist)
    try:
        #change the url to https://httpbin.org/ip that doesnt block anything
        r = requests.get('https://www.indeed.com.au/data-jobs', headers=headers, proxies={'http' : 'http://'+proxy,'https': 'https://'+proxy }, timeout=1.5)
        proxy_list.append(proxy)
    except:
        pass
    return proxy

def main():
    """Run the main program"""
    records = []
    values = 0
    url = 'https://www.indeed.com.au/data-jobs'

    proxylist = getProxies()

    print("Extracting best proxies...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(extract, proxylist)

    print(proxy_list)
    
    # Create template for CSV file
    with open('results.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Job Title', 'Company', 'Location', 'Salary', 'Posting Date', 'Extract Date', 'Summary', 'Description', 'Job Url'])

    new_proxy = proxy_list[0]
    #check them all with futures super quick
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(extract, proxylist)
    
    # Data Scraping
    while True:
        try:
            response = requests.get(url, headers=headers, proxies={'http' : 'http://'+new_proxy,'https': 'https://'+new_proxy})
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

        except requests.exceptions.RequestException as e:
            print(e)
            pass

        
        # Save the data to CSV
        with open('results.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(records) 
        
        values = values + len(records)
        print("Total Scraped: " + str(values))
        records = []
            
        try:
            url = 'https://www.indeed.com.au' + soup.find('a', {'aria-label': 'Next'}).get('href')
        except AttributeError:
            # This shouldn't be called until all proxies from list are depleted. (quick fix im going to sleep and letting it run)
            print("CAPTA OR PROXY ISSUE")
            proxylist = getProxies()

            print("Extracting best proxies again...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(extract, proxylist)
            print(proxy_list)
            

# Proxy hopping to avoid indeed detecting scraping
# get the list of free proxies

def getProxies():
    r = requests.get('https://free-proxy-list.net/')
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find('tbody')
    proxies = []
    for row in table:
        if row.find_all('td')[4].text =='elite proxy':
            proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
            proxies.append(proxy)
        else:
            pass
    return proxies


main()
