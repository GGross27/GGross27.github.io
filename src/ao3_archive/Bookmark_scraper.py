from bs4 import BeautifulSoup

def google_bookmark_scraper(export_file): 
    open("fic_links.txt", "w").close()
    #"5_28_26_bookmarks.html"
    with open(export_file, "r", encoding="utf-8") as file:   
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    folder_name = ["fanfic", "fic series", "oneshots"]
    links = []

    try:
        for dt in soup.find_all('dt'):
            for name in folder_name:
                h3 = dt.find('h3')
                if h3 is None:
                    continue        
                if h3.text in folder_name:
                    child_links = dt.find('dl')        
                    for child_dt in child_links.find_all('dt'):   
                        link = child_dt.find('a')['href']
                        if link not in links:
                            links.append(link)
                        
        with open("fic_links.txt", "w") as file2:
            for link in links:
                if link not in file2:  #prob need to debug
                    file2.write(link + "\n")

    except Exception as e:
        print(e)
