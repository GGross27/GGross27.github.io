from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import datetime
from time import sleep

def get_session():
    load_dotenv()
    username = os.getenv('AO3_USERNAME')
    password = os.getenv('AO3_PASSWORD')
    session = requests.Session()
    
    sleep(2)
    
    login_page = session.get('https://archiveofourown.org/users/login')
    soup = BeautifulSoup(login_page.text, 'html.parser')
    token = soup.find('input', {'name': 'authenticity_token'})['value']

    response = session.post('https://archiveofourown.org/users/login', data={
        'user[login]': username,
        'user[password]': password,
        'authenticity_token': token}, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'})
    
    print(f'[{datetime.datetime.now()}] -- {response.url}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))         # should NOT be the login page if successful
    print(f'[{datetime.datetime.now()}] -- {response.status_code}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8")) # should be 200
    response_text = 'logout' in response.text
    print(f'[{datetime.datetime.now()}] -- {response_text}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
    
    return session, response.status_code