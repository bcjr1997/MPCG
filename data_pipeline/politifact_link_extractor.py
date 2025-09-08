import requests
import logging
import re
import csv
import os
import argparse
import json
import time
import random
import spacy
import spacy_fastlang # Do not remove this. This is for language_detector
from bs4 import BeautifulSoup
from multiprocessing import Pool
from constants.politifact import POLITIFACT_CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def extract_all_politifact_links(args):
    url, PAGE_LIMIT = args['url'], args['page_limit']
    try:
        list1 = [3, 5, 7]
        sleep_timer = random.choice(list1)
        time.sleep(sleep_timer)
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')
        personalities = set()
        articles = set()
        # Gather Personalities and Articles from all HREF first
        for list_item in soup.find_all("li", {"class": "o-listicle__item"}):
            hrefs = list_item.find_all("a")
            personality = hrefs[0].get("href")
            article = hrefs[1].get("href")
            stubs = re.split('/', article)
            assert len(stubs) == 8
            try:
                # is_valid = translator.detect(stubs[6]).lang == 'en'
                nlp = spacy.load('en_core_web_sm')
                nlp.add_pipe("language_detector") 
                text = ' '.join(stubs[6].split('-')[:-1])
                doc = nlp(text)
                is_valid = doc._.language == 'en'
                logging.info(f"Stub: {stubs[6]} | Formatted Stub: {text} | Language: {doc._.language} | Valid: {is_valid} ")
                if is_valid:
                    personalities.add(personality)
                    articles.add(article)
            except:
                raise ValueError(article)
        
        # Get next page link and place it in the array
        new_stub_url = None
        page_number = None
        for button in soup.find_all("a", {"class": "c-button c-button--hollow"}):
            page_number_results = re.findall('\\?page=[0-9]*', button.get("href"))
            if len(page_number_results) > 0 :
                page_number = int(re.sub('\\?page=', '', page_number_results[0]))
            if button.text == 'Next' and page_number is not None and page_number <= PAGE_LIMIT: # 50 pages because it is not that old yet
                new_stub_url = "https://www.politifact.com/factchecks/list/" + button.get("href")
                
        return new_stub_url, new_stub_url is not None, personalities, articles, page_number
    except Exception as e:
        raise e
    
def get_all_politifact_links(args):

    SAVE_PATH = args.save_path
    PAGE_LIMIT = args.page_limit

    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    # Save current args to output
    with open(f"{SAVE_PATH}/argsparse_config.json", 'w') as file:
        json.dump(vars(args), file)
        file.close()

    urls = POLITIFACT_CONFIG['urls']
    personalities = set()
    articles = set()
    is_valid = True
    current_page_number = 1
    with Pool() as pool:
        while is_valid:
            inputs = [{'url': url, 'page_limit': PAGE_LIMIT} for url in urls]
            outputs = pool.map(extract_all_politifact_links, inputs)
            none_arr = []
            new_urls = []
            for url, is_next_url_available, extracted_personalities, extracted_articles, page_number in outputs:
                none_arr.append(is_next_url_available)
                if is_next_url_available:
                    new_urls.append(url)
                    personalities = personalities.union(extracted_personalities)
                    articles = articles.union(extracted_articles)
                    current_page_number = page_number
                    
            if len(new_urls) == 0:
                is_valid = False
            else:
                logging.info(f"New URLs found. Continuing the process. Page: {current_page_number} / {PAGE_LIMIT}")
                urls = new_urls

    logging.info(f'Finish mining links for Politifact. Page limit is {PAGE_LIMIT} for all classes')

    # Save Personalities
    logging.info(f"Saving Personalities under politifact_personalities_links.csv")
    with open(os.path.join(SAVE_PATH, 'politifact_personalities_links.csv'), 'w') as file:
        writer = csv.writer(file)
        for url_stub in personalities:
            writer.writerow(['https://www.politifact.com' + url_stub])
        file.close()
    logging.info(f"Done saving to politifact_personalities_links.csv")

    # Save Articles
    logging.info(f"Saving Articles under politifact_article_links.csv")
    with open(os.path.join(SAVE_PATH, 'politifact_article_links.csv'), 'w') as file:
        writer = csv.writer(file)
        for url_stub in articles:
            writer.writerow(['https://www.politifact.com' + url_stub])
        file.close()
    logging.info(f"Done saving to politifact_article_links.csv")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Politifact Link Extractor (Step 1)')
    parser.add_argument('--save_path', type=str, default=os.path.join('script_outputs', 'politifact-raw'), help='Script output location')
    parser.add_argument('--page_limit', type=int, default=50, help='Page Limit for Scrapping in PolitiFact')

    args = parser.parse_args()
    get_all_politifact_links(args)