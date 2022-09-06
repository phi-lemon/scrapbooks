import requests
from bs4 import BeautifulSoup
import re
import csv

url = 'http://books.toscrape.com/catalogue/dune-dune-1_151/index.html'
response = requests.get(url)
response.encoding = "utf-8"

if response.ok:
    soup = BeautifulSoup(response.text, features="html.parser")
else:
    print("The requested page is unreachable")


def product_info():
    """
    Get product details from the Product Information table
    :return: dict
    """
    product_information_table = soup.find("table", class_="table-striped")
    ths = product_information_table.findAll('th')  # product caracteristic name
    tds = product_information_table.findAll('td')  # product caracteristic detail
    return {k.text: v.text for k, v in zip(ths, tds)}


def review_rating():
    """
    Get rating (string) from page and convert it to an integer
    :return: int: book rating
    """
    rating_str = soup.find("p",  class_="star-rating")['class'][1]
    rating_int = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    return rating_int[rating_str]


def number_available():
    """
    get the availability and extracts the number of books in stock from the string
    :return: string
    """
    availability = product_info()['Availability']
    try:
        nb_available = re.search(r'(\d)', availability).group(0)
    except AttributeError:
        nb_available = ""  # todo check all products
    return nb_available


title = soup.find('h1').text
product_description = soup.find("div", id="product_description").find_next_siblings("p")[0].text
category = soup.find("li",  class_="active").find_previous_sibling().text.strip()

image_url = soup.find("div", id="product_gallery").find('img')['src']
image_url = "http://books.toscrape.com" + image_url[5:]  # concat domain name + uri


def single_product_to_csv():
    with open('data/product.csv', mode='w', newline='') as csv_file:
        fieldnames = ['product_page_url', 'universal_ product_code (upc)', 'title', 'price_including_tax', 'price_excluding_tax', 'number_available',
                      'product_description', 'category', 'review_rating', 'image_url']
        writer = csv.DictWriter(csv_file, delimiter=';', quotechar='"', fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'product_page_url': url,
                         'universal_ product_code (upc)': product_info()['UPC'],
                         'title': title,
                         'price_including_tax': product_info()['Price (incl. tax)'],
                         'price_excluding_tax': product_info()['Price (excl. tax)'],
                         'number_available': number_available(),
                         'product_description': product_description,
                         'category': category,
                         'review_rating': review_rating(),
                         'image_url': image_url})


single_product_to_csv()





