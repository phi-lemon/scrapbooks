import requests
from bs4 import BeautifulSoup
import re
import csv
from rich.progress import Progress, SpinnerColumn, TextColumn


def number_available(availability):
    """
    get the availability and extracts the number of books in stock from the string
    :param availability: string
    :return: string
    """
    try:
        nb_available = re.search(r'(\d+)', availability).group(0)
    except AttributeError:
        nb_available = ""
    return nb_available


def get_product_data(url):
    """
    get all the product data from a product page
    :param url: string
    :return: dict
    """
    response = requests.get(url)
    response.encoding = "utf-8"
    soup = ""
    if response.ok:
        soup = BeautifulSoup(response.text, features="html.parser")
    else:
        print("The requested page is unreachable")

    # main product information table
    product_information_table = soup.find("table", class_="table-striped")
    ths = product_information_table.findAll('th')  # product caracteristic name
    tds = product_information_table.findAll('td')  # product caracteristic detail
    product_infos = {k.text: v.text for k, v in zip(ths, tds)}

    rating_str = soup.find("p", class_="star-rating")['class'][1]
    rating_int = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}  # to match string rating with integers
    image_url = soup.find("div", id="product_gallery").find('img')['src']

    product = dict()
    product['product_page_url'] = url
    product['upc'] = product_infos['UPC']
    product['title'] = soup.find('h1').text
    product['price_including_tax'] = product_infos['Price (incl. tax)']
    product['price_excluding_tax'] = product_infos['Price (excl. tax)']
    product['number_available'] = number_available(product_infos['Availability'])
    try:
        product['product_description'] = soup.find("div", id="product_description").find_next_siblings("p")[0].text
    except AttributeError:
        product['product_description'] = ''
    product['category'] = soup.find("li",  class_="active").find_previous_sibling().text.strip()
    product['rating'] = rating_int[rating_str]
    product['image_url'] = "http://books.toscrape.com" + image_url[5:]  # concat domain name + uri

    return product


def products_to_csv(category, urls):
    """
    write product details to a csv file
    :param category: string, products category
    :param urls: string, product url
    :return: None
    """
    with open('data/' + category + '.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['product_page_url', 'universal_ product_code (upc)', 'title', 'price_including_tax', 'price_excluding_tax', 'number_available',
                      'product_description', 'category', 'review_rating', 'image_url']
        writer = csv.DictWriter(csv_file, delimiter=';', quotechar='"', fieldnames=fieldnames)
        writer.writeheader()
        for url in urls:
            product = get_product_data(url)
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


def get_paginate_urls(category):
    """
    list all paginate urls of a category
    :param category: name of the category (as written in the category url)
    :return: list
    """
    urls = ["http://books.toscrape.com/catalogue/category/books/" + category + "/index.html"]
    pagination = 2
    last_url = False
    while not last_url:
        url = "http://books.toscrape.com/catalogue/category/books/" + category + "/page-" + str(pagination) + ".html"
        response = requests.get(url)
        pagination += 1
        if response.ok:
            urls.append(url)
            last_url = False
        else:
            last_url = True
    return urls


def get_products_urls(page):
    """
    list all product links in a category page
    :param page: string, url of the category
    :return: list
    """
    response = requests.get(page)
    soup = ""
    product_urls = []
    if response.ok:
        soup = BeautifulSoup(response.text, features="html.parser")
    else:
        print("The requested page is unreachable")

    product_titles = soup.find_all("h3")
    for i in range(len(product_titles)):
        product_url = product_titles[i].find('a')['href']
        product_url = "http://books.toscrape.com/catalogue/" + product_url[9:]  # concat domain name + uri
        product_urls.append(product_url)
    return product_urls


def get_all_products_urls(category):
    """
    list all product links found in all pages of a category
    :param category: string, url of the category
    :return: list
    """
    urls = []
    for page in get_paginate_urls(category):
        for url in get_products_urls(page):
            urls.append(url)
    return urls


def category_to_csv(category):
    products_to_csv(category, get_all_products_urls(category))


def get_category_list():
    response = requests.get('http://books.toscrape.com/index.html')
    response.encoding = "utf-8"
    soup = ""
    if response.ok:
        soup = BeautifulSoup(response.text, features="html.parser")
    else:
        print("The requested page is unreachable")
    cat_list = []
    nav = soup.find("ul", class_="nav-list").find("ul")
    for link in nav.findAll('a'):
        cat = link.get('href').split('/')
        cat_list.append(cat[3])
    return cat_list


def scrape_all():
    categories_list = get_category_list()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        for category in categories_list:
            task = progress.add_task(description="Scraping " + category + " books...", total=100)
            category_to_csv(category)
            while not progress.finished:
                progress.update(task, advance=1)
    print("Done! All csv files are in the \"data\" folder")


if __name__ == '__main__':
    scrape_all()
