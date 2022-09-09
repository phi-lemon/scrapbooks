import requests
from bs4 import BeautifulSoup
import re
import csv
import pandas as pd
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console, Text
from rich.table import Table
import shutil
from pathlib import Path


def make_soup(url: str):
    """ Make a beautifulsoup object from url """
    response = requests.get(url)
    if response.ok:
        return BeautifulSoup(response.content, "html.parser")
    else:
        print("The requested page is unreachable")


class ProductData:
    """ Extracts product data and put it in a dict """
    def __init__(self, url: str):
        self.url = url
        self.soup = make_soup(url)
        self.product = self.get_data()

    @staticmethod
    def number_available(availabitilty: str):
        """
        Get the number of books in stock from the availibility paragraph
        :param availabitilty: text scraped from product page
        :return: number of items in stock (string)
        """
        try:
            nb_available = re.search(r'(\d+)', availabitilty).group(0)
        except AttributeError:
            nb_available = ""
        return nb_available

    def get_data(self):
        """
        extracts product data from product page
        :return: product data in a dict
        """
        # main product information html table
        product_information_table = self.soup.find("table", class_="table-striped")
        ths = product_information_table.findAll('th')  # product caracteristic name
        tds = product_information_table.findAll('td')  # product caracteristic detail
        product_infos = {k.text: v.text for k, v in zip(ths, tds)}

        rating_str = self.soup.find("p", class_="star-rating")['class'][1]
        rating_int = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}  # to match string rating with integers
        image_url = self.soup.find("div", id="product_gallery").find('img')['src']

        product = dict()
        product['product_page_url'] = self.url
        product['upc'] = product_infos['UPC']
        product['title'] = self.soup.find('h1').text
        product['price_including_tax'] = product_infos['Price (incl. tax)']
        product['price_excluding_tax'] = product_infos['Price (excl. tax)']
        product['number_available'] = self.number_available(product_infos['Availability'])
        try:
            product['product_description'] = self.soup.find("div", id="product_description").find_next_siblings("p")[0].text
        except AttributeError:
            product['product_description'] = ''
        product['category'] = self.soup.find("li", class_="active").find_previous_sibling().text.strip()
        product['rating'] = rating_int[rating_str]
        product['image_url'] = "http://books.toscrape.com" + image_url[5:]  # concat domain name + uri

        return product


class ProductImg:
    """ Save a product image to disc """
    def __init__(self, img_url: str, filename: str, category: str):
        self.img_url = img_url
        self.filename = filename
        self.category = category

    def download_img(self):
        """
        Download the image
        :return: None
        """
        r = requests.get(self.img_url, stream=True)
        img_dir = Path.cwd() / 'data' / 'img' / self.category
        if not Path.exists(img_dir):
            img_dir.mkdir(parents=True)
        if r.status_code == 200:
            # Preventing the downloaded image’s size from being zero.
            r.raw.decode_content = True
            with open('data/img/' + self.category + '/' + self.filename + '.jpg', 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            print('Image ' + self.filename + ' Couldn\'t be retrieved')


def write_to_disk(category: str, urls: list):
    """
    Loads all products of a category: first write products details to a csv file, then save products images to disk
    :param category: products category
    :param urls: list of products urls
    :return: None
    """
    # Write csv
    with open('data/' + category + '.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['product_page_url', 'universal_ product_code (upc)', 'title', 'price_including_tax', 'price_excluding_tax', 'number_available',
                      'product_description', 'category', 'review_rating', 'image_url']
        writer = csv.DictWriter(csv_file, delimiter=';', quotechar='"', fieldnames=fieldnames)
        writer.writeheader()
        for url in urls:
            product = ProductData(url).product
            writer.writerow({'product_page_url': product['product_page_url'],
                             'universal_ product_code (upc)': product['upc'],
                             'title': product['title'],
                             'price_including_tax': product['price_including_tax'],
                             'price_excluding_tax': product['price_excluding_tax'],
                             'number_available': product['number_available'],
                             'product_description': product['product_description'],
                             'category': product['category'],
                             'review_rating': product['rating'],
                             'image_url': product['image_url']})
    # Download images
    for url in urls:
        product = ProductData(url).product
        img_name = re.sub(r'[^a-zA-Z0-9 ]', '', product['title']).replace(' ', '_')
        img = ProductImg(product['image_url'], img_name, product['category'])
        img.download_img()


class SiteUrls:
    """ Methods to get products page urls from a category """
    def __init__(self, category):
        self.category = category

    def get_paginate_urls(self):
        """
        list all paginate urls of a category
        :return: list
        """
        urls = ["http://books.toscrape.com/catalogue/category/books/" + self.category + "/index.html"]
        pagination = 2
        last_url = False
        while not last_url:
            url = "http://books.toscrape.com/catalogue/category/books/" + self.category + "/page-" + str(pagination) + ".html"
            response = requests.get(url)
            pagination += 1
            if response.ok:
                urls.append(url)
                last_url = False
            else:
                last_url = True
        return urls

    def get_all_products_urls(self):
        """
        list all product links found in all pages of a category
        :return: list
        """
        product_urls = []
        for page in self.get_paginate_urls():
            soup = make_soup(page)
            product_titles = soup.find_all("h3")
            for i in range(len(product_titles)):
                product_url = product_titles[i].find('a')['href']
                product_url = "http://books.toscrape.com/catalogue/" + product_url[9:]  # concat domain name + uri
                product_urls.append(product_url)
        return product_urls


def load_category(category: str):
    """
    Loads all the products of a category
    :param category: category
    :return: None
    """
    category_urls = SiteUrls(category)
    write_to_disk(category, category_urls.get_all_products_urls())


def get_category_list():
    """
    List all the categories from the site
    :return: list
    """
    soup = make_soup('http://books.toscrape.com/index.html')
    cat_list = []
    nav = soup.find("ul", class_="nav-list").find("ul")
    for link in nav.findAll('a'):
        cat = link.get('href').split('/')
        cat_list.append(cat[3])
    return cat_list


categories_list = get_category_list()


def scrape_all():
    """
    Main function that loops through all the categories and scrapes the products data
    :return:
    """
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        for category in categories_list:
            cat_name = category.split('_')[0]
            task = progress.add_task(description="Scraping " + cat_name + " books...", total=100)
            load_category(category)
            while not progress.finished:
                progress.update(task, advance=1)
    console = Console()
    text = Text("\nDone! All csv files are in the \"data\" folder\n")
    text.stylize("bold green")
    console.print(text)


def data_summary():
    """ Function to call atfer scrape_all() to get a summary of scraped data """
    df_list = []
    for cat in categories_list:
        try:
            df_list.append(pd.read_csv('data/' + cat + '.csv', sep=';', header=0))
        except FileNotFoundError:
            print("File not found for category " + cat)
    df = pd.concat(df_list)
    df['price_including_tax'] = df['price_including_tax'].replace('£', '', regex=True)
    df['price_including_tax'] = df['price_including_tax'].astype('float')

    table = Table(title="Data summary")

    table.add_column("Data", justify="right", style="cyan", no_wrap=True)
    table.add_column("Value", style="sandy_brown")

    table.add_row("Total products", str(df.shape[0]))
    table.add_row("Total available items in stock", str(df['number_available'].sum()))
    table.add_row("Average stock per product", str(round(df['number_available'].mean(), 1)))
    table.add_row("Min stock per product", str(df['number_available'].min()))
    table.add_row("Max stock per product", str(df['number_available'].max()))
    table.add_row("Average price (incl. tax)", str(round(df['price_including_tax'].mean(), 2)))
    table.add_row("Min price (incl. tax)", str(df['price_including_tax'].min()))
    table.add_row("Max price (incl. tax)", str(df['price_including_tax'].max()))

    console = Console()
    console.print(table)


if __name__ == '__main__':
    scrape_all()
    data_summary()

