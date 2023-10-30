import json
from config import Config
import pandas as pd

class JsonFunction:
    @staticmethod
    def save_data(data_dict: dict, location: str) -> None:
        """
        Save json file into memory
        :param data_dict: data which needs to be saved as json
        :param location: location where json is saved
        :return: None
        """
        with open(location, "w") as f:
            json.dump(data_dict, f)

    @staticmethod
    def load_data(location: str) -> dict:
        """
        load data from json
        :param location: location where json is saved
        :return: list of name
        """
        with open(location, "r") as f:
            json_dict = json.load(f)
        return json_dict

    @staticmethod
    def json_to_csv(location: str):
        """
        Convert json to csv
        :param location: where csv needs to be saved
        :return: Null
        """
        data = JsonFunction.load_data(Config.data_location)[Config.data_json_name]

        df = pd.DataFrame(data=data)

        df.to_csv(location, index=False, encoding="utf-8-sig")

