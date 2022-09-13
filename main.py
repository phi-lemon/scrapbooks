import re
import csv
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Text
import shutil
from pathlib import Path
from scrapbooks_utils import *


class ProductData:
    """ Extracts product data from an URL and put it in a dict """
    def __init__(self, url: str):
        self.url = url
        self.soup = make_soup(url)
        self.product = self.get_data()

    @staticmethod
    def number_available(availability: str):
        """
        Get the number of books in stock from the availibility paragraph
        :param availability: text scraped from product page
        :return: number of items in stock (string)
        """
        try:
            nb_available = re.search(r'(\d+)', availability).group(0)
        except AttributeError:
            nb_available = None
        return nb_available

    def get_data(self):
        """
        extracts product data from product page
        :return: product data in a dict
        """
        product = dict()
        product['title'] = self.soup.find('h1').text
        product['product_page_url'] = self.url

        image_url = self.soup.find("div", id="product_gallery").find('img')['src']
        product['image_url'] = "http://books.toscrape.com" + image_url[5:] if image_url else None

        # Main product information html table ###################################
        product_information_table = self.soup.find("table", class_="table-striped")
        ths = product_information_table.findAll('th')  # product caracteristic name
        tds = product_information_table.findAll('td')  # product caracteristic detail
        product_infos = {k.text: v.text for k, v in zip(ths, tds)}

        # Rating ##########################################################
        rating_int = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}  # to match string rating with integers
        try:
            rating_str = self.soup.find("p", class_="star-rating")['class'][1]
            product['rating'] = rating_int[rating_str]
        except IndexError:
            product['rating'] = None

        try:
            product['product_description'] = self.soup.find("div", id="product_description").find_next_siblings("p")[0].text
        except AttributeError:
            product['product_description'] = None

        product['category'] = self.soup.find("li", class_="active").find_previous_sibling().text.strip()

        try:
            product['upc'] = product_infos['UPC']
        except KeyError:
            product['upc'] = None

        try:
            product['price_including_tax'] = product_infos['Price (incl. tax)']
        except KeyError:
            product['price_including_tax'] = None

        try:
            product['price_excluding_tax'] = product_infos['Price (excl. tax)']
        except KeyError:
            product['price_excluding_tax'] = None

        product['number_available'] = self.number_available(product_infos['Availability'])

        return product


class LoadProductImg:
    """ Get product img from an URL and save it to disk """
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
            r.raw.decode_content = True  # otherwise download size will be 0
            with open('data/img/' + self.category + '/' + self.filename + '.jpg', 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            print('Image ' + self.filename + ' Couldn\'t be retrieved')


class LoadCategoryContents:
    """ Methods to load all product contents (data & img) from a category """
    def __init__(self, category: str):
        self.category = category
        self.product_urls = self.get_all_products_urls()

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
        self.product_urls = []  # Essential! Adding self.product_urls = self.get_all_products_urls() in __init__ is not enough. But why ???
        for page in self.get_paginate_urls():
            soup = make_soup(page)
            product_titles = soup.find_all("h3")
            for i in range(len(product_titles)):
                product_url = product_titles[i].find('a')['href']
                product_url = "http://books.toscrape.com/catalogue/" + product_url[9:]  # concat domain name + uri
                self.product_urls.append(product_url)
        return self.product_urls

    def products_data_to_csv(self):
        """
        Loop through all products of a category and write each product data to a csv file
        :return: None
        """
        # Write csv
        data_path = Path.cwd() / 'data'
        if not Path.exists(data_path):
            data_path.mkdir(parents=True)

        with open('data/' + self.category + '.csv', mode='w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['product_page_url', 'universal_ product_code (upc)', 'title', 'price_including_tax', 'price_excluding_tax', 'number_available',
                          'product_description', 'category', 'review_rating', 'image_url']
            writer = csv.DictWriter(csv_file, delimiter=';', quotechar='"', fieldnames=fieldnames)
            writer.writeheader()
            for url in self.product_urls:
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

    def products_imgs_to_disk(self):
        """
        Loop through all products of a category and save each product img to disk
        :return: None
        """
        for url in self.product_urls:
            product = ProductData(url).product
            img_name = re.sub(r'[^a-zA-Z0-9 ]', '', product['title']).replace(' ', '_')
            img = LoadProductImg(product['image_url'], img_name, product['category'])
            img.download_img()


def scrape_all():
    """
    Main function that loops through all the categories and loads all products data and images
    :return: None
    """
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        for category in get_category_list():
            cat_name = category.split('_')[0]
            task = progress.add_task(description="Scraping " + cat_name + " books...", total=100)
            category_contents = LoadCategoryContents(category)
            category_contents.products_data_to_csv()
            category_contents.products_imgs_to_disk()
            while not progress.finished:
                progress.update(task, advance=1)
    console = Console()
    text = Text("\nDone! All csv files are in the \"data\" folder\n")
    text.stylize("bold green")
    console.print(text)
    

if __name__ == '__main__':
    scrape_all()
    data_summary()
