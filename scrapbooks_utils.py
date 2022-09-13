"""
Utility functions imported in main scraping script
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from rich.console import Console
from rich.table import Table


def make_soup(url: str):
    """ Make a beautifulsoup object from url """
    response = requests.get(url)
    if response.ok:
        return BeautifulSoup(response.content, "html.parser")
    else:
        print("The requested page is unreachable")


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


def data_summary():
    """ Function to call atfer scraping to get a summary of fetched data """
    df_list = []
    for cat in get_category_list():
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
