from lxml.html import fromstring
from bs4 import BeautifulSoup
from datetime import datetime
from itertools import cycle
from random import randint
import concurrent.futures
from time import sleep
import traceback
import requests
import csv

# Author: Diego Portela
# Webscrapper program for indeed.com.au
# This program was developed for education purposes only!
# THE CODE SHARED IN THIS REPOSITORY SHOULD NEVER BE USED OR EXPLOITED
# Note: Headers are not used in this program but can be implemented
# If there is difficulties connecting to Indeed.com.au

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
proxy_list = []
current_proxy = ''

def extract(proxy):
    global proxy_list
    #this was for when we took a list into the function, without conc futures.
    #proxy = random.choice(proxylist)
    try:
        r = requests.get('https://www.indeed.com.au/data-jobs', headers=headers, proxies={'http' : 'http://'+proxy,'https': 'https://'+proxy }, timeout=1.5)
        proxy_list.append(proxy) #Populate the global proxy_list
    except:
        pass
    return proxy

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

def render_proxy():
    # get all the proxies
    proxies = getProxies()
    # use only working good proxies
    print("extracting best proxies... ")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(extract, proxies)
    print(proxy_list)


def create_template():
    # Create template for CSV file
    # Note: this will overwrite any data!
    print('creating template CSV...')
    with open('results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Job Title', 'Company', 'Location', 'Salary', 'Posting Date', 'Extract Date', 'Description', 'Job Url'])


# set a new proxy from the proxy list
def get_proxy():
    global current_proxy
    if (len(proxy_list) > 0):
        current_proxy = proxy_list.pop(0)
    else:
        print("repopulating proxy list")
        render_proxy()
        return get_proxy()

def proxy_type(proxy):
    proxies = {
        'http' : 'http://'+proxy,
        'https': 'https://'+proxy
    }
    return proxies


# Get the details of found card, returns record
def get_record(card):
    # Get the description of the card
    url = 'https://indeed.com.au' + card.get('href')
    response = ''
    try:
        response = requests.get(url, headers=headers, proxies=proxy_type(current_proxy))
    except requests.exceptions.RequestException as e:
        print('Connection error, getting new proxy')
        get_proxy()
        # retry same card request
        return get_record(card)

    print("Description URL Status: " + str(response.status_code))
    response.encoding = response
    soup = BeautifulSoup(response.text, 'html.parser')
    get_desc = soup.find('div', {"class":"jobsearch-jobDescriptionText"})
    description = ''

    for child in get_desc.findChildren(recursive=True):
        description = description + (child.getText()) + " "

    # Get the other useful information of the card

    try:
        title_temp = (card.find('h2', {"class": "jobTitle"}).find_all('span'))
        if (len(title_temp) > 1):
            title = title_temp[1].text.strip()
        else:
            title = title_temp[0].text.strip()
    except:
        title = ""

    try:
        company = (card.find("span", {"class": "companyName"}).text.strip())
    except:
        company = ""

    try:
        location = (card.find("div", {"class": "companyLocation"}).text.strip())
    except:
        location = ""

    try:
        date = card.find('span', 'date').text
    except:
        date = ""
        
    try:
        salary = card.find('span', {"class": "salary-snippet"}).text.strip()
    except:
        salary = ''

    today = datetime.today().strftime("%Y-%m-%d")
    real_url = response.url
    
    record = (title, company, location, salary, date, today, description, real_url)
    return record

def data_save(records):
    # Save the data to CSV
    with open('results.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(records) 

def main():
    records = []
    total_scraped = 0
    url = 'https://www.indeed.com.au/data-jobs'

    # Set the proxies
    get_proxy()
    
    # Create the CSV Template
    create_template()

    # Main Loop
    while True:
        response = ''
        try:
            response = requests.get(url, headers=headers, proxies=proxy_type(current_proxy))
        except requests.exceptions.RequestException as e:
            get_proxy()

        if (response != ''):
            response.encoding = response
            print("New URL Status: " + str(response.status_code))
            print(response.url)
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all('a', 'tapItem')
    
            for card in cards:
                record = get_record(card)
                records.append(record)

            # Save the data
            data_save(records)
            total_scraped = total_scraped + len(records)
            print("Total Scraped: " + str(total_scraped))

            # Reset the records list (already saved to CSV)
            records = []

            # Go to next page after scraping
            try:
                next_loc = soup.find('a', {'aria-label': 'Next'}).get('href')
                if (next_loc == ''):
                    break
                else:
                    url = 'https://www.indeed.com.au' + next_loc
            except AttributeError:
                get_proxy()
        else:
            print('invalid server reponse')
            get_proxy()
        
            
    

main()
