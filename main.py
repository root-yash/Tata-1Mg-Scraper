import argparse
import sys
sys.path.append("Src")
import os, get_1mg_data
from utils import JsonFunction
from config import Config
from extract_links import extract_links

parser = argparse.ArgumentParser()

parser.add_argument("--excel_location", type=str, help="location of excel file",
                    default=None)
parser.add_argument("--sheet_name", type=str, help="name of excel sheet",
                    default=None)
parser.add_argument("--product_link", type=bool, help="direct product link of not",
                    default=None)
parser.add_argument("--column_name", type=str, help="column in excel containing drug name",
                    default="Name")

parser = parser.parse_args()


if __name__ == "__main__":
    if not os.path.exists(Config.json_link_output):
        extract_links(parser.excel_location, parser.sheet_name, parser.column_name, parser.product_link)

    get_1mg_data.Get1MgData(parser.product_link)

    JsonFunction.json_to_csv(Config.result_loc)



