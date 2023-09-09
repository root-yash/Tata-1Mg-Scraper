from config import Config
from utils import JsonFunction
import os
import asyncio
from tqdm import tqdm
from ratelimiter import RateLimiter
from bs4 import BeautifulSoup
from urllib import parse
import requests
import nest_asyncio

nest_asyncio.apply()


class Get1MgData:
    def __init__(self):
        self.links = JsonFunction.load_data(Config.json_link_output)[Config.json_link_name]
        self.data_dict = []

        if os.path.exists(Config.data_location):
            print("loading previous data")
            self.data_dict = JsonFunction.load_data(Config.data_location)[Config.data_json_name]

        print("________________Getting Information____________")
        asyncio.get_event_loop().run_until_complete(self.get_details(self.links))


    async def get_details(self, links: list) -> None:
        """
        Save details in json for all links
        :param links: list of link whose medicine composition we want
        :return: Null
        """

        for idx, link in tqdm(enumerate(links)):
            drug_details = {
                "name": parse.unquote(link.split(Config.link_split_value)[1])
            }

            try:
                header = {"user-agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98) XX"}
                parsed_html = BeautifulSoup(requests.get(link, headers=header).text, 'html.parser')

                # if there is suggestion list
                if parsed_html.find("ul", {"class": "gl style__list-suggestion___3ZmkX"}):
                    suggestion_list = parsed_html.find("ul", {"class": "gl style__list-suggestion___3ZmkX"})
                    new_link = Config.parent_domain + suggestion_list.find('a', href=True)['href']

                    # load the correct page
                    parsed_html = BeautifulSoup(requests.get(new_link, headers=header).text, 'html.parser')

                product_card = parsed_html.find("div", {"class": "row style__grid-container___3OfcL"})

                drug_link = Config.parent_domain + product_card.find('a', href=True)['href']

                drug_details.update(
                    await self.get_drug_detail(drug_link)
                )
            except:
                drug_details.update(
                    {
                        "composition": None
                    }
                )

            self.data_dict.append(drug_details)

            if (idx + 1) % 10 == 0 or len(links) == idx + 1:
                # update link list
                JsonFunction.save_data(
                    {
                        Config.json_link_name: links[idx + 1:]
                    },
                    Config.json_link_output
                )
                # Save Details
                JsonFunction.save_data(
                    {
                        Config.data_json_name: self.data_dict
                    },
                    Config.data_location
                )

    @RateLimiter(max_calls=1, period=1)
    async def get_drug_detail(self, link) -> dict:
        """
        return Dictionary containing drug details
        :param link: link of drug page
        :return: dict with drug details
        """
        drug_detail = {}
        header = {"user-agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98) XX"}
        parsed_html = BeautifulSoup(requests.get(link, headers=header).text, 'html.parser')

        # tata 1mg name
        item_name = (self.__get_text(parsed_html, "h1", "ProductTitle__product-title___3QMYH")
                     or
                     self.__get_text(parsed_html, "h1", "DrugHeader__title-content___2ZaPo"))


        # Item Company
        company_name = (self.__get_text(parsed_html, "div", "ProductTitle__manufacturer___sTfon")
                        or
                        self.__get_text(parsed_html, "div", "DrugHeader__meta-value___vqYM0"))

        # composition of drug
        composition = self.__get_href_text(parsed_html, "div", "saltInfo DrugHeader__meta-value___vqYM0")

        # selling price
        selling_price = self.__get_text(
            parsed_html,
            "span",
            "PriceBoxPlanOption__offer-price___3v9x8 PriceBoxPlanOption__offer-price-cp___2QPU_"
        ) or self.__get_text(
            parsed_html,
            "span",
            "DrugPriceBox__best-price___32JXw"
        )

        # MRP
        mrp = self.__get_text(
            parsed_html,
            "span",
            "PriceBoxPlanOption__margin-right-4___2aqFt PriceBoxPlanOption__stike___pDQVN"
        ) or self.__get_text(
            parsed_html,
            "span",
            "DrugPriceBox__slashed-price___2UGqd"
        ) or self.__get_text(
            parsed_html,
            "div",
            "PriceDetails__mrp-tag___3WdTI"
        )

        # aggregate result
        drug_detail.update({
            "item_name": item_name,
            "item_company": company_name,
            "composition": composition,
            "selling_price": selling_price,
            "mrp": mrp
        })

        return drug_detail

    def __get_href_text(self, parsed_html, tag: str, class_value: str):
        try:
            parsed_tag = parsed_html.find(tag, {"class": class_value})
            value = parsed_tag.find('a', href=True).text

        except:
            value = None
        return value

    def __get_text(self, parsed_html, tag: str, class_value: str):
        try:
            value = parsed_html.find(tag, {
                "class": class_value
            }).text

        except:
            value = None
        return value

