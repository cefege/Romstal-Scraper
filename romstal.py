from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from playwright.sync_api import sync_playwright
import markdownify

def crawler(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()

        # Open new page
        page = context.new_page()

        # Go to Cartuseria
        page.goto(url, wait_until="networkidle", timeout=0)
        #time.sleep(10)
        
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        return soup, url


def extract_data(soup, url):
    #Elements
    title = 'n/a'
    header_1 = 'n/a'
    page_type = 'n/a'
    description_word_count = 0
    description_links = 0
    faq_exists = False
    products_count = 0
    #url = 'n/a'
    cannonical_url = 'n/a'
    breadcrumb_text = 'n/a'
    breadcrumb_links = 'n/a'

    #Check page type
    try:
        _type = soup.find("body")
        _type = _type['data-page']
        page_type = _type
    except:
        pass

    #Grab Page Title:
    try:
        _title_extract = str(soup.find('title').get_text())
        title =_title_extract
    except:
        pass

    #Grab Header 1:
    try:
        _header_extract = soup.select('.t-heading-color')[0].get_text()
        header_1 = _header_extract.strip()
    except:
        pass

    #Grab description + faq word count
    try:
        if "category" in page_type:
            description_html = soup.select('.blured-desc')
        if 'product' in page_type:
            description_html = soup.select('.blured-specs')
        #Convert list to string
        description_html = description_html[0]

        links_count = len(description_html.findAll('a'))
        description_links = links_count

        word_list = description_html.get_text().split()
        word_count = len(word_list)

        description_word_count = word_count

    #Number of words in description and FAQ  

    except:
        pass

    #Check if FAQ exist
    try:
        len(soup.find("div", {"itemtype": "https://schema.org/Question"}))
        faq_exists = True

    except:
        pass

    #Extract cannonical URL if it exists
    try:
        cannonical_url = soup.find("link", {"rel": "canonical"})['href']
    except:
        pass

    #Extract number of products
    try:
        if "category" in page_type:
            x = soup.select('#middle-column > div.category-options.clearfix > div.clearfix.bottom-category-section > div > span > strong:nth-child(2)')
            #convert list into string
            x = x[0].get_text()
            products_count = x
        
        if "product" in page_type:
            products_count = 1
    except:
        pass

    #Extract breadcrumbs

    try:
        # bs4 soup slect the following css element "box-breadcrumbs"
        breadcrumbs = soup.select('.box-breadcrumbs')[0]

        # select all hrefs values from the element
        breadcrumbs_links = breadcrumbs.select('a')

        breadcrumb_text = []
        breadcrumb_links = []
        for link in  breadcrumbs_links:
            breadcrumb_text.append(link.get_text())
            if link.get('href') != None:
                if 'https://' in link.get('href'):
                    breadcrumb_links.append(link.get('href'))
                else:
                    breadcrumb_links.append('https://www.romstal.ro/' + link.get('href')) # Convert relative 
        
        # remove first element from the list
        breadcrumb_text.pop(0)
        breadcrumb_links.pop(0)

        # convert list to string with seprarator
        breadcrumb_text = ' > '.join(breadcrumb_text)
        breadcrumb_links = ' > '.join(breadcrumb_links)


    except:
        pass

    df = pd.DataFrame({ 'Meta Title': title, 
                        'H1': header_1,
                        'Tip Pagina':page_type,
                        'Cuvinte Descriere': description_word_count,
                        'Linkuri Interne Descriere': description_links,
                        'Exista FAQ': faq_exists,
                        'Numar Produse': products_count,
                        'URL': url,
                        'URL Cannonical': cannonical_url,
                        'breadcrumb_text':breadcrumb_text,
                        'breadcrumb_links': breadcrumb_links
                        }, 
                        index=[0])

    csv_path = Path('romstal.csv')

    if csv_path.is_file():
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, mode='a', header=True, index=False)

### Extracts products list function
def extract_product_list(soup, url):
    #Extract product list
    product_list = soup.select('.picture')
    product_list = list(set([x.find('a')['href'] for x in product_list]))
    product_list = ['https://www.romstal.ro/' + x for x in product_list]

url_list = pd.read_csv('url_list.csv').values.tolist()

## Extract normal data
for url in tqdm(url_list):
    to_extract = crawler(url[0])
    extract_data(to_extract[0], to_extract[1])


### Extracts products list
# for url in tqdm(url_list):
#     to_extract = crawler(url[0])
#     extract_product_list(to_extract[0], to_extract[1])
