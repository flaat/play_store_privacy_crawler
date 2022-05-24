###############################################################
## Python crawler 1.0 for google play for data extraction    ##
## Flavio Giorgi                                             ##
###############################################################

###import statement##
from lxml import etree
from io import StringIO
import requests
from queue import Queue
import play_scraper as pl
from selenium import webdriver
import regex as re
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading as td
import time


class crawler():

    def __init__(self,csv_name):
        ###variable###
        self.CSV_APP_PRIVACY_NAME = csv_name
        self.TO_CSV_NUMBER = 10
        self.QUEUE_MAX_SIZE = 10000
        global visited_links
        global WAIT_CYCLE
        self.apps_privacy_dataset = []
        self.driver = webdriver.Firefox()
        self.restart_links_number = 0
        self.MAX_LINKS = 100

    ###get_store_infos###
    def get_store_infos(self,id,str):
        info = pl.details(id)
        temp_page = self.driver.get(str)
        try:
            privacy_page = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@jsname='Hly47e']")))
        except Exception:
            return None
        privacy_page.click()
        privacy_elements = []
        privacy_elements = self.driver.find_elements_by_xpath("//li[@class='BCMWSd']")
        i = 0
        while privacy_elements == [] and i < WAIT_CYCLE:
            time.sleep(0.005)
            privacy_elements = self.driver.find_elements_by_xpath("//li[@class='BCMWSd']")
            i+=1
        regular_expression = re.compile("(<li class=\"BCMWSd\"><span>|</span></li>)")
        privacy_elements_list = [re.sub(regular_expression,"",element.get_attribute("outerHTML")) for element in privacy_elements]
        self.apps_privacy_dataset.append([info.get('app_id'),privacy_elements_list,info.get('price'),info.get("iap"),info.get("iap_range")])




    ###get_links###
    def get_links(self,tree):
        return_list = []
        # This will get the anchor tags <a href...>
        refs = tree.xpath("//a")
        # Get the url from the ref
        links = [link.get('href', '') for link in refs]
        for l in links:
            if "https://play.google.com" not in l:
                str = "https://play.google.com"+l
            c.acquire()
            if  "/apps/details?id=" in str and str not in visited_links:
                if len(self.apps_privacy_dataset)%self.TO_CSV_NUMBER == 0:
                    with open(self.CSV_APP_PRIVACY_NAME, "a") as f:
                        writer = csv.writer(f)
                        writer.writerows(self.apps_privacy_dataset)
                        self.apps_privacy_dataset = []
                return_list.append(str)
                visited_links.add(str)
                c.notify_all()
                c.release()
                self.restart_links_number +=1
                self.get_store_infos(str.split("?id=")[1],str)
            else:
                c.notify_all()
                c.release()
            str = ""
        return return_list


    ###explore###
    def explore(self,init):
        with open(self.CSV_APP_PRIVACY_NAME, "w") as f:
            writer = csv.writer(f)
        # Set explicit HTMLParser
        parser = etree.HTMLParser()
        link_queue = Queue(maxsize=self.QUEUE_MAX_SIZE)
        link_queue.put(init)

        while not link_queue.empty():
            if (self.restart_links_number>self.MAX_LINKS):
                    self.driver.quit()
                    self.driver = webdriver.Firefox()
                    self.restart_links_number = 0
            print("QUEUE_SIZE :", link_queue.qsize())
            print("visited links:", len(visited_links))
            page_link = link_queue.get()
            print("Exploring: ",page_link)
            page = requests.get(page_link)
            if page.status_code == 200:
                html = page.content.decode("utf-8")
                tree = etree.parse(StringIO(html), parser=parser)
                [link_queue.put(l) for l in self.get_links(tree)]
            else:
                print("Page skipped")
        print("Empty QUEUE")
        
        
       
if __name__ == "__main__":
    #list of entry points
    link_list = ["https://play.google.com/store/apps"]
    visited_links = set()
    c = td.Condition()
    WAIT_CYCLE = 3000
    i = 0
    for link in link_list:
        # Example call

        p = td.Thread(target=crawler(str(i)+".csv").explore, args=(link,))
        p.start()
        i+=1
