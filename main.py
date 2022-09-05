import requests
from bs4 import BeautifulSoup

url = 'http://books.toscrape.com/catalogue/dune-dune-1_151/index.html'
response = requests.get(url)
response.encoding = "utf-8"

if response.ok:
    soup = BeautifulSoup(response.text, features="html.parser")
    product_information_table = soup.find("table", class_="table-striped")
    ths = product_information_table.findAll('th')
    tds = product_information_table.findAll('td')
    product_info = {k.text: v.text for k, v in zip(ths, tds)}
    print(product_info)

else:
    print("La page demandée n'est pas accessible")



# product_page_url
# universal_ product_code (upc)
# title
# price_including_tax
# price_excluding_tax
# number_available
# product_description
# category
# review_rating
# image_url


# if __name__ == '__main__':
#     print('PyCharm')
