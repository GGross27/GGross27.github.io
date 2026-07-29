import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import cookies
import bookmark_scraper
import database
import traceback
import random
import argparse
import os
import datetime

def scrape_work(soup, link):
    sleep(random.randint(2, 5))
    try: 
        work_info_group = soup.select_one('dl.work.meta.group')
        
        work_serial_num = link.split('/')[4].strip()
        work_ID = "AO3W_" + (work_serial_num)
        epub_download = "https://archiveofourown.org/downloads/"+ work_serial_num + "/title.epub"
                
        current_chapter = soup.find('div', class_='chapter')
        current_chapter_num = str(current_chapter.get('id')).split('-')[1] if current_chapter else 1

        preface = soup.find('div', class_='preface')
        title_text = preface.find('h2', class_= 'title').text.strip()
        byline = preface.find('h3', class_='byline')
        authors = byline.find_all('a') if byline else []
        author_text = ', '.join(a.get_text(strip=True) for a in authors) if authors else 'Anonymous'
        
        # byline = preface.find('h3', class_='byline')
        # byline_text = byline.get_text(" ", strip=True)
        # if byline_text == "": 
        #     author_text = byline.find('a').text
        # else: 
        #     author_text = byline_text
        
        summary_module = preface.find('div', class_='summary')
        blockquote = summary_module.find('blockquote', class_='userstuff')
        summary = "\n\n".join(p.get_text(" ", strip=True)for p in blockquote.find_all("p"))

    except Exception as e:
        print(f"[{datetime.datetime.now()}] -- Failed getting work info group: {traceback.format_exc()}", file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
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
        
        series = work_info_group.find('span', class_='series')
        if series is None:
            series_id = None
        else: 
            series_section = series.find('span', class_='position')
            series_id = "AO3S_" + series_section.find('a')['href'].split('/')[2]
        
        stats = work_info_group.find('dd', class_='stats')
        info = stats.find('dl', class_='stats')
        published = info.find('dd', class_='published').get_text(strip=True)
        chapter_count = info.find('dd', class_='chapters').get_text(strip=True).split('/')[0]
        
        if int(chapter_count) > 1:
            status = info.find('dt', class_='status').get_text(strip=True).strip(':')[0] # Completed: or Updated:
            updated = info.find('dd', class_='status').get_text(strip=True) # status date
        else: 
            status = None
            updated = None
        
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
            "Published": published,
            "Status": status,
            "Status Date": updated,
            "Series_id": series_id,
            "Chapter Count": int(chapter_count),
            "Current Chapter": current_chapter_num,
            "Summary": summary,
            "Completed": False,
            "Category_ID": None
        }
        
        return results
    except Exception as e:
        print(f"[{datetime.datetime.now()}] -- Failed getting fandom tags: {traceback.format_exc()}", file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
        return None

def scrape_series(soup, link):
    sleep(random.randint(5, 10))
    try: 
        series_serial_num = link.split('/')[4].strip()
        series_ID = "AO3S_" + (series_serial_num)
        
        main = soup.find('div', class_='series-show')
        title_text = main.find('h2', class_='heading').get_text(strip=True)
        
        content = main.find('div', class_='wrapper')
        inner_content = content.find('dl', class_='series')
        
        creator_dt = inner_content.find('dt', string='Creator:')
        if creator_dt is None:
            author_text = 'Anonymous'
        else:
            dd = creator_dt.find_next_sibling('dd')
            if dd is None:
                author_text = 'Anonymous'
            else:
                authors = dd.find_all('a')
                if not authors:
                    author_text = 'Anonymous'
                else:
                    author_text = ', '.join(a.get_text(strip=True) for a in authors)
                    
        # creator_dt = inner_content.find('dt', string='Creator:')
        # author_text = creator_dt.find_next_sibling('dd').find('a').get_text(strip=True)
           
                
        stats = inner_content.find('dd', class_='stats').find('dl', class_='stats')
        works_count = stats.find('dd', class_='works').get_text(strip=True)
        begun_dt = stats.find('dt', string='Series Begun:')
        series_begun = begun_dt.find_next_sibling('dd').get_text(strip=True)
        
        updated_dt = stats.find('dt', string='Series Updated:')
        series_updated = updated_dt.find_next_sibling('dd').get_text(strip=True)
        
        description_dt = stats.find('dt', string='Description:')
        description_dd = description_dt.find_next_sibling('dd')
        blockquote = description_dd.find('blockquote', class_='userstuff')
        description = "\n\n".join(p.get_text(" ", strip=True) for p in blockquote.find_all("p"))
        
        notes_dt = stats.find('dt', string='Notes:')
        notes_dd = notes_dt.find_next_sibling('dd')
        blockquote = notes_dd.find('blockquote', class_='userstuff')
        notes = "\n\n".join(p.get_text(" ", strip=True) for p in blockquote.find_all("p"))
        
        complete_dt = stats.find('dt', string='Complete:')
        completed_status = complete_dt.find_next_sibling('dd').get_text(strip=True)

        if completed_status == "Yes":
            completed = True
        else: 
            completed = False
        
        # get works list from series page
        series_works = []
        for work in soup.find_all('li', class_='work'):
            heading = work.find('h4', class_='heading')
            work_link = heading.find('a')['href']
            work_title = heading.find('a').text
            work_id = 'AO3W_' + work_link.split('/')[2]
            series_works.append({
                'work_id': work_id,
                'work_title': work_title,
                'work_link': 'https://archiveofourown.org' + work_link
            })   
            
        results = {
            "Title": title_text,
            "Author": author_text,
            "url": link,
            "ID": series_ID,
            "Created": series_begun,
            "Updated": series_updated,
            "Works Count": works_count,
            "Completed": completed,
            "Category_ID": None,
            "Works List": series_works,
            "Description": description,
            "Notes": notes
        }
        
        return results
    
    except Exception as e:
        print(f"[{datetime.datetime.now()}] -- Failed getting series main info group: {traceback.format_exc()}", file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
        return None

def derive_category(chapter_count:int, completed: bool):
    '''
    Given the chapter_count and completed parameters, get the filter category for (non series) 
    works AO3 Links. Returns the category_id.
    
    Category ID Guide:
    1 --> Oneshot
    2 --> Ongoing Fanfic
    3 --> Complete Fanfic
    4 --> Series
    '''
    
    if chapter_count <= 3 and completed:
        return 1  # Oneshot
    if chapter_count >= 3 and not completed:   
        return 2  # Ongoing
    if chapter_count >= 3 and completed:       
        return 3  # Completed
    return 2  # fallback: treat ambiguous as Ongoing

    
def extract_id(url):
    parts = url.split('/')
    if '/series/' in url:
        return 'AO3S_' + parts[4]
    if '/works/' in url:
        return 'AO3W_' + parts[4]
    return None

def clean_url(url):
    if '/chapters/' in url:
        url = url.split('/chapters/')[0]
    if '/collections/' in url:
        url = "/".join(url.split('/')[:3] + url.split('/')[5:])
        
    url = url.split('#')[0]
    url = url.split('?')[0]
    
    return url

def main(args, batchNum=None):
    if args.single:
        print(f'\n\n[{datetime.datetime.now()}] -- Processing single scrape for {args.single}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
        links = [args.single]
    elif args.batch:
        print(f'\n\n[{datetime.datetime.now()}] -- Processing batch scrape from google bookmarks html file: {args.batch}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
        links = bookmark_scraper.google_bookmark_scraper(args.batch)  # your existing bookmark parser
    elif args.txt or args.failed:
        links = open(args.txt).read().splitlines()
        count = 0 # track number of urls added; testing aid
        if args.start:
            print(f'\n\n[{datetime.datetime.now()}] -- Processing txt scrape from txt file: {args.txt}, start line: {args.start}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
            links = links[args.start - 1:]  # --start 51 starts at line 51
            count = args.start - 1
        else:
            print(f'\n\n[{datetime.datetime.now()}] -- Processing txt scrape from txt file: {args.txt}, start line: 1', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
    
    session, cookies_status = cookies.get_session() 
    
    if cookies_status == 525:
        return
    
    work_results_batch = []
    series_results_batch = []
    
    CONSECUTIVE_BLOCK_LIMIT = 3  # stop after this many 525s in a row
    consecutive_blocks = 0 
    
    
    for url in links:
        count += 1
    # url = "https://archiveofourown.org/works/28616283/chapters/70346880#main"
        raw_url = url
        url = clean_url(url)
        print(f'[{datetime.datetime.now()}] -- Processing ({count}) link: {url}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
        
        response = session.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'})
        status_code = response.status_code
        print(f'[{datetime.datetime.now()}] -- {status_code}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
        
        if status_code == 525:
            consecutive_blocks += 1
            open("src/logs/failed_links.txt", "a").write(f'{raw_url}\n')
            print(f"[{datetime.datetime.now()}] -- Cloudflare block {consecutive_blocks}/{CONSECUTIVE_BLOCK_LIMIT} for {url}", file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
            database.insert_failed_link(url, id=extract_id(raw_url), status_code=525)

            if consecutive_blocks >= CONSECUTIVE_BLOCK_LIMIT:
                print(f'[{datetime.datetime.now()}] -- Too many consecutive blocks — stopping batch. Try again in 30 minutes.', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
                break  # stop the whole loop, save what you have
            
            sleep(60)
            continue
        
        if status_code == 200:  # OK
            soup = BeautifulSoup(response.text, 'html.parser')
            if '/series/' in url:
                try: 
                    series_info = scrape_series(soup, url)
                    sleep(random.randint(5, 10))
                    
                    if series_info is None or isinstance(series_info, str):
                        error_Message = f"[{datetime.datetime.now()}] -- Scrape failed for {url}: {series_info}"
                        print(error_Message, file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
                        open("src/logs/failed_links.txt", "a").write(f'{raw_url}\n')
                        database.insert_failed_link(url, id=extract_id(raw_url), error_msg="Series scrape returned None")
                        continue
                        
                    series_info["Category_ID"] = 4
                    series_info["url"] = raw_url
                    
                    print(f'[{datetime.datetime.now()}] -- Adding to Series database...', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))                      
                    database.upsert_series(series_info)
                    
                    if args.failed:
                        resolve_failed_link(url) 
                except Exception as e:
                    print(f'[{datetime.datetime.now()}] -- Data could not be extracted: {e}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
            else: 
                try:
                    work_info = scrape_work(soup, url)
                    sleep(random.randint(5, 10))
                    
                    if work_info is None or isinstance(work_info, str):
                        error_Message = f"[{datetime.datetime.now()}] -- Scrape failed for {url}: {work_info}"
                        print(error_Message, file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
                        open("src/logs/failed_links.txt", "a").write(f'{raw_url}\n')
                        database.insert_failed_link(url, id=extract_id(raw_url), error_msg="Works scrape returned None")                        
                        continue
                    
                    if args.currentchapter: 
                        work_info['Current Chapter'] = args.currentchapter
                        
                    work_info["url"] = raw_url
                    
                    chapter_count = work_info['Chapter Count']
                    status = work_info['Status']

                    if status == 'Completed':
                        work_info["Completed"] = True
                        
                    work_info["Category_ID"] = derive_category(chapter_count,  work_info["Completed"])
                    print(f'[{datetime.datetime.now()}] -- Adding to Works database...', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))
                    database.upsert_work(work_info) 
                    
                    if args.failed:
                        resolve_failed_link(url) 
                except Exception as e:
                    print(f'[{datetime.datetime.now()}] -- Data could not be extracted: {e}', file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))      
        # HTTP failures
        elif status_code == 404: # Not Found
            open("src/logs/failed_links.txt", "a").write(f'{raw_url}\n')
            database.insert_failed_link(url, id=extract_id(raw_url), status_code=404)
        elif status_code == 403: # Forbidden; Might not appear while using cookies
            open("src/logs/failed_links.txt", "a").write(f'{raw_url}\n')
            database.insert_failed_link(url, id=extract_id(raw_url), status_code=403)
        else:
            open("src/logs/failed_links.txt", "a").write(f'{raw_url}\n')
            database.insert_failed_link(url, id=extract_id(raw_url), status_code=status_code)
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', type=str)   # one link
    parser.add_argument('--batch',  type=str)   # bookmarks html file path
    parser.add_argument('--txt',    type=str)   # txt file path
    parser.add_argument('--start', type=int, default=0)  # optional, defaults to 0
    parser.add_argument('--currentchapter', type=int, default=1)  # optional, defaults to 1
    parser.add_argument('--failed', type=str) # retry the failed links
    args = parser.parse_args()
    main(args)
    
    
'''
To Do:
switch from using csv to directly adding the data into their respective tables
this should be done here and in database.py
    ---> test the most recent scraper + database.py code
    

fix the data collection method in the html pages
    html form --> js collection --> python grab+ process into sql
    
figure out how to display data from sql databases onto a website
'''