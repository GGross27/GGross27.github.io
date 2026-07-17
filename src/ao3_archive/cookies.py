from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup

def get_session():
    load_dotenv()
    username = os.getenv('AO3_USERNAME')
    password = os.getenv('AO3_PASSWORD')
    session = requests.Session()
    
    login_page = session.get('https://archiveofourown.org/users/login')
    soup = BeautifulSoup(login_page.text, 'html.parser')
    token = soup.find('input', {'name': 'authenticity_token'})['value']

    response = session.post('https://archiveofourown.org/users/login', data={
        'user[login]': username,
        'user[password]': password,
        'authenticity_token': token}, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'})
    
    print(response.url)         # should NOT be the login page if successful
    print(response.status_code) # should be 200
    print('logout' in response.text)
    
    return session