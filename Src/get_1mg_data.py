from config import Config
from utils import JsonFunction
import os
import asyncio
from tqdm import tqdm
from ratelimiter import RateLimiter
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib import parse
import requests
import nest_asyncio

nest_asyncio.apply()


class Get1MgData:
    def __init__(self, product_link: bool):
        self.links = JsonFunction.load_data(Config.json_link_output)[Config.json_link_name]
        self.data_dict = []

        if os.path.exists(Config.data_location):
            print("loading previous data")
            self.data_dict = JsonFunction.load_data(Config.data_location)[Config.data_json_name]

        print("________________Getting Information____________")
        asyncio.get_event_loop().run_until_complete(self.get_details(self.links, product_link))


    async def get_details(self, links: list, product_link: bool) -> None:
        """
        Save details in json for all links
        :param links: list of link whose medicine composition we want
        :return: Null
        """

        for idx, link in tqdm(enumerate(links)):
            try:
                if product_link:
                    drug_details = {
                        "name": parse.unquote(link.split(Config.link_split_value)[0])
                    }
                    drug_details.update(
                        await self.get_drug_detail(link)
                    )
                else:
                    drug_details = {
                        "name": parse.unquote(link.split(Config.link_split_value)[1])
                    }
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

        # selling price
        selling_price = self.__get_text(
            parsed_html,
            "span",
            "PriceBoxPlanOption__offer-price___3v9x8 PriceBoxPlanOption__offer-price-cp___2QPU_"
        ) or self.__get_text(
            parsed_html,
            "div",
            "DrugPriceBox__best-price___32JXw"
        ) or self.__get_text(
            parsed_html,
            "div",
            "PriceDetails__discount-div___nb724"
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
        ) or self.__get_text(
            parsed_html,
            "span",
            "DiscountDetails__discount-price___Mdcwo"
        )

        # Package Size
        pack_size = self.__get_text(
            parsed_html,
            "div",
            "DrugPriceBox__quantity___2LGBX"
        ) or self.__get_text(
            parsed_html,
            "span",
            "PackSizeLabel__single-packsize___3KEr_"
        )


        # composition of drug
        composition = self.__get_href_text(
            parsed_html,
            "div",
            "saltInfo DrugHeader__meta-value___vqYM0"
        )

        # aggregate result
        drug_detail.update({
            "item_name": item_name,
            "item_company": company_name,
            "composition": composition,
            "selling_price": selling_price,
            "mrp": mrp,
            "package_size": pack_size,
        })

        try:
            #Information
            information = self.__get_product_information(parsed_html)

            # aggregate result
            drug_detail.update({
                "composition": composition or information.pop("Key Ingredients", None),
                "key_benefits": information["Key Benefits"],
                "introduction": information["Introduction"],
                "side_effects": information.get("Side Effects", None),
                "direction_of_use": information.get("Directions for Use", None)
            })
        except:
            return drug_detail

        return drug_detail

    def __get_product_information(self, parsed_html) -> dict:
        """
        :param parsed_html: Bs4 parsed html
        :return: Find information on the product and return it
        """
        blocks = {}
        first = True
        if parsed_html.find("div", {"class": "ProductDescription__product-description___1PfGf"}):
            parsed_html = parsed_html.find("div", {"class": "ProductDescription__product-description___1PfGf"})

            if len(parsed_html.find_all("strong")[0].nextSibling) > 20 and first:
                blocks["Introduction"] = parsed_html.find_all("strong")[0].text + " " + parsed_html.find_all("strong")[0].nextSibling
                first = False

            for idx, heading in enumerate(parsed_html.find_all("strong")):
                values = []

                for sibling in heading.find_next_siblings():
                    if sibling.name == "br":
                        text = self.get_br_text(sibling)
                    else:
                        text = sibling.text

                    if sibling.name == "strong":
                        break

                    if text != None:
                        values.append(text.strip())


                if len(values) != 0:
                    if first:
                        blocks["Introduction"] = ",".join(values)
                        first = False
                        continue
                    blocks[heading.text.split(":")[0]] = ",".join(values)
        else:
            parsed_html = parsed_html.find("div", {"class": "DrugPage__main-content___MrJho"})
            object_name = ["Introduction", " ", "Key Benefits", " ", "Side Effects", " ", "Directions for Use"]
            for data, obj_name in zip(parsed_html.find_all("div", {"class": "DrugOverview__content___22ZBX"})[:7], object_name):
                blocks[obj_name] = data.get_text(",", strip=True)

        return blocks

    def get_br_text(self, br):
        next_s = br.nextSibling

        if not (next_s and isinstance(next_s, NavigableString)):
            return None

        next2_s = next_s.nextSibling
        if next2_s and isinstance(next2_s, Tag) and next2_s.name == 'br':
            text = str(next_s).strip()
            if text:
                return next_s

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

