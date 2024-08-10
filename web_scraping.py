import requests
import pkg_resources
from bs4 import BeautifulSoup
import schedule
import time
from selenium import webdriver  
from selenium.webdriver.common.by import By
from playwright.sync_api import sync_playwright
import pandas as pd
import asyncio
import re
from email.message import EmailMessage
from typing import Collection, List, Tuple, Union

import aiosmtplib

cities = {
    'RedwoodCity': '108490965842587'
}

carCodes = {
    'Nissan': ('2621742507840619', 
               {
                '350z': '2229736997088203'
                }),
    
}

HOST = "smtp.gmail.com"
# https://kb.sandisk.com/app/answers/detail/a_id/17056/~/list-of-mobile-carrier-gateway-addresses
# https://www.gmass.co/blog/send-text-from-gmail/
CARRIER_MAP = {
    "verizon": "vtext.com",
    "tmobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    "at&t": "txt.att.net",
    "boost": "smsmyboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "uscellular": "email.uscc.net",
}


def getUrl(city, make, model):
    if make == None:
        marketplaceUrl = f'https://www.facebook.com/marketplace/{cities[city]}/search/?sortBy=creation_time_descend&query={model}&exact=true'
    else:
        marketplaceURL = f'https://www.facebook.com/marketplace/{cities[city]}/vehicles?sortBy=creation_time_descend&make={carCodes[make][0]}&model={carCodes[make][1][model]}&exact=false'
    return marketplaceURL

def singleSearch(city, make, model):  
    marketplaceURL = getUrl(city, make, model)
    with sync_playwright() as p:
        # Open a new browser page.
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        # Navigate to the URL.
        page.goto(marketplaceURL)
        # Wait for the page to load.
        time.sleep(2)

        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        parsed = []
        listings = soup.find_all('div', class_='x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24')
        print(f"Found {len(listings)} listing for model {model} in {city}")
        for listing in listings:
            try:
                # Get the item image.
                image = listing.find('img', class_='xt7dq6l xl1xv1r x6ikm8r x10wlt62 xh8yej3')['src']
                # Get the item title from span.
                title = listing.find('span', 'x1lliihq x6ikm8r x10wlt62 x1n2onr6').text
                # Get the item price.
                price = listing.find('span', 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x676frb x1lkfr7t x1lbecb7 x1s688f xzsf02u').text
                # Get the item URL.
                post_url = 'facebook.com' + listing.find('a', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 xggy1nq x1a2a7pz x1heor9g xt0b8zv x1hl2dhg x1lku1pv')['href']
                # Get the item location.
                location = listing.find('span', 'x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1j85h84').text
                # Append the parsed data to the list.
                if make != None:
                    miles = listing.find('div', class_='x9f619 x78zum5 xdt5ytf x1qughib x1rdy4ex xz9dl7a xsag5q8 xh8yej3 xp0eagm x1nrcals').find_all('div', class_='x1gslohp xkh6y0r')[-1].find('span', 'x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1j85h84').text
                    parsed.append({
                        'image': image,
                        'title': title,
                        'price': price,
                        'post_url': post_url,
                        'location': location,
                        'miles': miles
                    })
                else:
                    parsed.append({
                        'image': image,
                        'title': title,
                        'price': price,
                        'post_url': post_url,
                        'location': location
                    })

                print('Adding listing')
            except:
                print('Could not add listing')
                pass

        # Close the browser.
        browser.close()
        # Return the parsed data as a JSON.
        results = []
        for item in parsed:
            if make != None:
                results.append({
                    'name': item['title'],
                    'price': item['price'],
                    'location': item['location'],
                    'miles': item['miles'],
                    'title': item['title'],
                    'image': item['image'],
                    'link': item['post_url']
                })
            else:
                results.append({
                    'name': item['title'],
                    'price': item['price'],
                    'location': item['location'],
                    'title': item['title'],
                    'image': item['image'],
                    'link': item['post_url']
                })
        print(f'Number of results from current search: {len(results)}')
        return results
        
def retrySearch(user, city, make, model):
    searchResults = singleSearch(city, make, model)
    filename = f'{city}_{model}.csv'
    cachedResults = pd.read_csv(filename)
    tempCache = pd.DataFrame()
    textNotification = 'New listings:\n'
    count = 0
    
    newResults = {}
    for result in searchResults:
        if cachedResults.loc[(cachedResults['image'] == result['image'])].any().all():
            print('Repeated listing')
            continue

        newResults.append(result)
        count += 1

        # create notification for customer
        # textNotification += f'{(count + 1)}: For {result['price']}, {result['link']}\n'
    print(f'Number of new results: {len(newResults)}')
    newResults = pd.DataFrame(newResults)
    newResults = pd.concat([newResults, cachedResults], ignore_index=True)
    # send notification to customer

    newResults.to_csv(filename, index=False)

def setupPhoneNumber(name, phoneNumber, carrier):
    user = {'name': [name,], 'phonenumber': [phoneNumber], 'carrier': [carrier]}
    user = pd.DataFrame(user)
    allNumbers = pd.read_csv('phonenumbers.csv')
    allNumbers = pd.concat([allNumbers, user], ignore_index=True)
    allNumbers.to_csv('phonenumbers.csv', index=False)

def sendText(user, message):
    allNumbers = pd.read_csv('phonenumbers.csv')
    recipient = allNumbers.iloc[allNumbers['name'] == user]

async def send_txt(
    num: Union[str, int], carrier: str, email: str, pword: str, msg: str, subj: str
) -> Tuple[dict, str]:
    to_email = CARRIER_MAP[carrier]

    # build message
    message = EmailMessage()
    message["From"] = email
    message["To"] = f"{num}@{to_email}"
    message["Subject"] = subj
    message.set_content(msg)

    # send
    send_kws = dict(username=email, password=pword, hostname=HOST, port=587, start_tls=True)
    res = await aiosmtplib.send(message, **send_kws)  # type: ignore
    msg = "failed" if not re.search(r"\sOK\s", res[1]) else "succeeded"
    print(msg)
    return res

if __name__ == '__main__':
    _num = "7732267010"
    _carrier = "tmobile"
    _email = "junior1.alcantar@gmail.com"
    _pword = "pword"
    _msg = "Dummy msg"
    _subj = "Dummy subj"
    coro = send_txt(_num, _carrier, _email, _pword, _msg, _subj)
    # _nums = {"999999999", "000000000"}
    # coro = send_txts(_nums, _carrier, _email, _pword, _msg, _subj)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(coro)