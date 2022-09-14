from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console, Text
from scrapbooks_utils import ScrapUtils
from scrapbooks import LoadCategoryContents


def main():
    """
    Main function that loops through all the categories and loads all products data and images
    :return: None
    """
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        for category in ScrapUtils.get_category_list():
            cat_name = category.split('_')[0]
            task = progress.add_task(description="Scraping " + cat_name + " books...", total=100)
            category_contents = LoadCategoryContents(category)
            category_contents.products_data_to_csv()
            category_contents.products_imgs_to_disk()
            while not progress.finished:
                progress.update(task, advance=1)
    console = Console()
    text = Text("\nDone! csv files are in the \"data\" folder\n")
    text.stylize("bold green")
    console.print(text)

    # Print data summary to console
    ScrapUtils.data_summary()


if __name__ == '__main__':
    main()
