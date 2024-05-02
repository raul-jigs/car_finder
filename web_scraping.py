import requests
from bs4 import BeautifulSoup
import schedule
import time
from selenium import webdriver  

redwoodCityCode = '108490965842587'

def startSearching(city, query):
    marketplaceUrl = f'https://www.facebook.com/marketplace/{city}/search/?query={query}&exact=true'
    # r = requests.get(marketplaceUrl)

    # soup = BeautifulSoup(r.content, 'html.parser')
    # print(soup.prettify())
    # create webdriver object  
    driver = webdriver.Firefox()  
    
    # get google.co.in  
    driver.get(marketplaceUrl)  
    time.sleep(60)

startSearching(redwoodCityCode, '350z')