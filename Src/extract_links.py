import pandas as pd
from utils import JsonFunction
from urllib import parse
from config import Config


def extract_links(file_location: str, sheet_name: str, column_name: str, product_link: str) -> None:
    """
    Extract Medicine links to Json
    :param file_location: Location where Excel file is located
    :param sheet_name: Name of Excel sheet
    :param column_name: Column in which medicine name is present
    :return: None
    """
    links = []
    dataframe = pd.read_excel(file_location, sheet_name=sheet_name)[column_name]

    if product_link:
        links = dataframe.to_list()
    else:
        # convert name to link
        for name in dataframe.to_list():
            links.append(
                "https://www.1mg.com/search/all?name=" + parse.quote(name.strip())
            )

    JsonFunction.save_data(
        {
            Config.json_link_name: links
        },
        Config.json_link_output
    )
