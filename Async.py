import requests
import re
import time
#using DOM TREE
import lxml.etree
import threading
from queue import Queue
from bs4 import BeautifulSoup
output_list = []
start_time = 0

#fix broken links
def resolve(url):
         #resolving broken links
        if re.match(r"^//www\..+", url):
            i = page_url.split(':')
            new_url = i[0] +':' + url
            return new_url
        elif re.match(r"^/\w+.+",url):
            new_url = page_url + url
            return new_url            
        else:
            return url

#Domain check
# def Domain_check(url):
#     domain = page_url.split('/')[2]
#     url_split = url.split('/')
#     if domain in url:
#         return 1
#     else:
#         return 0
    

#create data files
def create_data(name, data):
    f = open(name, 'w')
    f.write(data)
    f.close()

#Delete file content
def Delete_content(name):
    with open(name, 'w'):
        pass

#read file into a set
def file_to_set(name):
    results = set()
    with open(name, 'rt') as f:
        for line in f:
            results.add(line.strip())
    return results

#write set to a file
def set_to_file(data, name):
    Delete_content(name)
    for link in data:
        with open (name, 'a') as q:
            q.write(link + '\n')

#ASYNC CLASS    
class spider:
    #Class Variables
    base_url = ''
    queue_file =''
    crawled_file = ''
    queue = set()
    crawled = set()

    def __init__(self, base_url):
        start_time = time.perf_counter()
        spider.base_url = base_url
        spider.queue_file = 'queue'
        spider.crawled_file = 'crawled'

        spider.boot(self)
        spider.crawl('first spider', spider.base_url)

    def boot(self):
        create_data(spider.queue_file, spider.base_url)
        create_data(spider.crawled_file, '')
        create_data('html_content.txt', '')
        create_data('text_content.txt', '')
        spider.queue = file_to_set(spider.queue_file)
        spider.crawled = file_to_set(spider.crawled_file)

    #Crawl function
    def crawl(thread_name, url):
        if url not in spider.crawled:
            print( thread_name  + "  Now Crawling: " + url)
            print('Queue  ' +  str(len(spider.queue)) + "  ||  crawled " + str(len(spider.crawled)))
            spider.get_links(url)
            if url in spider.queue:
                spider.queue.remove(url)
            spider.crawled.add(url)

            #updating data files
            queue_copy = spider.queue.copy()
            crawled_copy = spider.crawled.copy()
            
            set_to_file(queue_copy, spider.queue_file)
            set_to_file(crawled_copy, spider.crawled_file)

            #getting html content
            try:
                html_content = requests.get(url).text
            except:
                return ''
            
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            spider.results(text_content,output_list)
            spider.output(html_content, text_content)
    # grabbing links from the page   
    def get_links(url):
        try:
            response = requests.get(url)
        except:
            return ''

        
        #Parsing response to DOM tree
        tree = lxml.etree.HTML(response.content)
        
        #Finding all the links in the page
        lnk = tree.findall(".//a")
        
        #getting all links that match our search
        for link in lnk:
            if link.get('href') is None:
                continue
            else:
                href = link.get('href')
            
            #checking if link matches format
            if re.match(r"^(?:((https|http)?:?(.+)?%?/(programmes|.+programmes|programmes.+|areas\-of\-study|courses|courses\-listing|programs|.+programs|programs.+|courses.+|.+courses|)/?([0-9]+).+$) | ((https|http)?://uoab(.+)?$) | ((https|http)?:?.+(\?|%).+?$))", href):
                continue
            # elif re.match(r"^(https|http)?://uoab(.+)?$", href):
            #     continue
            #elif re.match(r"^(https|http)?:?(.+)?/(majors|academics|programmes|.+programmes|programmes.+|areas\-of\-study|courses|courses\-listing|programs|.+programs|programs.+|courses.+|.+courses)/?(.+)?(page.+)?$", href):
            elif re.match(r"^(https|http)?:?(.+)?/(majors|academics|programmes|.+programmes|programmes.+/|areas\-of\-study|courses|courses\-listing|programs|.+programs|programs.+/|.+courses)/?(page.+)?/?(.+)?", href):
                href = resolve(href)
                if href in spider.queue:
                    continue
                elif href in spider.crawled:
                    continue
                #checking if domain name exist in href
                else:
                    # if Domain_check(href) == True:
                        print(f'queuing:  {href}')
                        spider.queue.add(href)
                    # else:
                    #     continue
            else:
                continue
    
    #processing my results
    def results(content,output_list):
        
        #opening my course dictionary
        with open("cour", "r") as f:
            line =  f.readlines()
        courses = []
        for i in line:
            if i != '\n':
                courses.append(i.strip())
        for course in courses:
            if course in content and course not in output_list:
                # print('[+] '+course)
                output_list.append(course)
            else:
                continue
    
    def output(html, content):
        with open('html_content.txt', 'a', encoding="utf-8") as h:
                h.write(html)
        with open('text_content.txt', 'a', encoding="utf-8") as f:
            f.write(content)

    #updating queue and crawled file:
    def Update_files(name1, name2, data1, data2):
        set_to_file(data1, name1)
        set_to_file(data2, name2)


NUMBER_OF_THREADS = 500
QUEUE_FILE = 'queue'
CRAWLED_FILE =  'crawled'
queue = Queue()

#ceating worker threads. dies after main exits
def create_threads():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target= job)
        t.daemon = True
        t.start()

#do the next job in queue and informs when it is done
def job():
    while True:
        url = queue.get()
        spider.crawl(threading.current_thread().name, url)
        queue.task_done()

#creating jobs. turning Each Queue link ino a new job
def create_jobs():
    
    #passing queue file to thread queue
    for link in file_to_set(QUEUE_FILE):
        queue.put(link)
    #eliminaing spider traffic jam by ensuring they all wait their turn
    queue.join()
    #updating state and making job creation continuous
    crawler()

#check if there are items in queue, if so, crawl the queue
def  crawler():
    queue_links = file_to_set(QUEUE_FILE)
    if len(queue_links) > 0:
        print(str(len(queue_links)) + 'links in the queue')
        create_jobs()
    else:
        stop_time = time.perf_counter()
        runtime = stop_time - start_time
        print(f'This University offers about {len(output_list)} courses. They can be seen above')
        print(output_list)
        print(runtime)
page_url = str(input('enter url: '))
spider(page_url)
create_threads()
crawler()
  

