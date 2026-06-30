import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import cookies
import Bookmark_scraper
import traceback
import random
import argparse


def scrape_work(soup, link):
    try: 
        sleep(random.randint(2, 5))
        work_info_group = soup.select_one('dl.work.meta.group')
        
        work_serial_num = link.split('/')[4].strip()
        work_ID = "AO3W_" + (work_serial_num)
        epub_download = "https://archiveofourown.org/downloads/"+ work_serial_num + "/title.epub"
                
        current_chapter = soup.find('div', class_='chapter')
        current_chapter_num = str(current_chapter.get('id')).split('-')[1] if current_chapter else 1

        preface = soup.find('div', class_='preface')
        title_text = preface.find('h2', class_= 'title').text.strip()
        byline = preface.find('h3', class_='byline')
        author_text = byline.find('a').text

    except Exception as e:
        print(f"Failed getting work info group: {traceback.format_exc()}")
        return None
    
    def get_tags(parent):
        result = []
        if parent is None:
            return result
    
        ul = parent.find('ul', class_='commas')
        if ul is None:
            return result 
        
        for li in ul.find_all('li'):
            tag = li.find('a', class_='tag')
            result.append(tag.text)
        return result

    try:
        fandoms = work_info_group.find('dd', class_='fandom')
        fandom_tags = get_tags(fandoms)
        
        relationships = work_info_group.find('dd', class_='relationship')
        relationship_tags = get_tags(relationships)
        
        characters = work_info_group.find('dd', class_='character')
        character_tags = get_tags(characters)
        
        additionals = work_info_group.find('dd', class_='freeform')
        additional_tags = get_tags(additionals)
        
        stats = work_info_group.find('dd', class_='stats')
        info = stats.find('dl', class_='stats')
        status = info.find('dt', class_='status').text.strip(':')
        chapter_count = info.find('dd', class_='chapters').text.split('/')[0]
        
        results = {
            "Title": title_text,
            "Author": author_text,
            "url": link,
            "download": epub_download,
            "ID": work_ID,
            "Fandom Tags": fandom_tags,
            "Relationship Tags": relationship_tags,
            "Character Tags": character_tags,
            "Additional Tags": additional_tags,
            "Status": status,
            "Chapter Count": int(chapter_count),
            "Current Chapter": current_chapter_num,
            "Completed": False,
            "Category_ID": None
        }
        
        return results
    except Exception as e:
        print(f"Failed getting fandom tags: {traceback.format_exc()}")
        return None

def scrape_series(soup):
    pass

def clean_work_info(work_info):   
    if work_info is None or isinstance(work_info, str):
        error_Message = f"Scrape failed for {url}: {work_info}"
        print(error_Message)
        failed_links.append((url, error_message))
        continue
    
    chapter_count = work_info['Chapter Count']
    status = work_info['Status']
    
    if status == 'Completed':
        work_info["Completed"] = True
        
    work_info["Category_ID"] = derive_category(chapter_count,  work_info["Completed"]) 
    
    return work_info

def derive_category(chapter_count:int, completed: bool):
    '''
    Given the chapter_count and completed parameters, get the filter category for (non series) 
    works AO3 Links. Returns the category_id.
    
    Category ID Guide:
    1 --> Oneshot
    2 --> Ongoing Fanfic
    3 --> Complete Fanfic
    4 --> Series
    5 --> Deleted Fanfic/Series
    6 --> Locked Fanfic/Series
    '''
    
    if chapter_count <= 3 and completed:
        return 1  # Oneshot
    if chapter_count >= 3 and not completed:   
        return 2  # Ongoing
    if chapter_count >= 3 and completed:       
        return 3  # Completed
    return 2  # fallback: treat ambiguous as Ongoing


def main(args, batchNum=None):
    session = cookies.get_session() 
    
    if args.single:
        links = [args.single]
    elif args.batch:
        links = Bookmark_scraper.parse(args.batch)  # your existing bookmark parser
    elif args.txt:
        links = open(args.txt).read().splitlines()
    
    
    work_results = []
    series_results = []
    failed_links = []
    
    # with open('test_batch.txt', 'r') as file:
    #     for line in file:
    #         links.append(line.strip('\n'))
    # # print(links)
    
    open('Works.csv', 'w').close()
    
    for url in links:
    # url = "https://archiveofourown.org/works/28616283/chapters/70346880#main"
    
        if '/chapters/' in url:
            url = url.split('/chapters/')[0] 
        url = url.split('#')[0]
        print(f'Processing link: {url}')
        
        response = session.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'})
        status_code = response.status_code
        print(status_code)
        if status_code == 200:  # OK
            soup = BeautifulSoup(response.text, 'html.parser')
            if '/series/' in url:
                # scrape_series(soup)
                category_id = 4
            else: 
                try: 
                    work_info = scrape_work(soup, url)
                    sleep(random.randint(5, 10))
                    work_info = clean_work_info(work_info)
                    work_results.append(work_info) 
                except Exception as e:
                    print("Data could not be extracted: ", e)
        elif status_code == 404: # Not Found
            category_id = 5
            failed_links.append((url, status_code))

        elif status_code == 403: # Forbidden
            category_id = 6
            #this migh not be needed if i used cookies
            failed_links.append((url, status_code))

    df = pd.DataFrame(work_results)
    df.to_csv("Works.csv", index=False)
    # return all the info needed for each link
    # this should be a full CSV
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', type=str)   # one link
    parser.add_argument('--batch',  type=str)   # bookmarks html file path
    parser.add_argument('--txt',    type=str)   # txt file path
    args = parser.parse_args()
    main(args)