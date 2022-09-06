import requests
from bs4 import BeautifulSoup
import single_product

# récupérer la liste des catégories (attribut href)


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
    for page in get_paginate_urls(category):
        return get_products_urls(page)


