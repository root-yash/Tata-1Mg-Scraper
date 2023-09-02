from config import Config
from utils import JsonFunction
import os, asyncio
from tqdm import tqdm
from pyppeteer import launch
from bs4 import BeautifulSoup
from urllib import parse
import nest_asyncio
nest_asyncio.apply()

class Get1MgData:
    def __init__(self):
        self.links = JsonFunction.load_data(Config.json_link_output)[Config.json_link_name]
        self.data_dict = []

        if os.path.exists(Config.data_json_name):
            print("loading previous data")
            self.data_dict = JsonFunction.load_data(Config.data_location)[Config.data_json_name]

        print("________________Getting Information____________")
        asyncio.get_event_loop().run_until_complete(self.get_details(self.links))

    async def get_drug_detail(self, link) -> dict:
        """
        return Dictionary containing drug details
        :param link: link of drug page
        :return: dict with drug details
        """
        drug_detail = {}
        browser = await launch()
        page = await browser.newPage()
        await page.goto(link)
        try:
            html = await page.evaluate('''() => {
                        return document.querySelector('.main-content').innerHTML;
                    }''')

            parsed_html = BeautifulSoup(html, 'html.parser')

            composition = parsed_html.find("div", {"class": "saltInfo DrugHeader__meta-value___vqYM0"})
            composition = composition.find('a', href=True).text

            drug_detail.update({
                "composition": composition
            })

        except:
            self.data_dict.update({"composition": None})

        await page.close()
        await browser.disconnect()
        await browser.close()

        return drug_detail

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

            browser = await launch()
            page = await browser.newPage()
            await page.goto(link)
            header = {"user-agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98) XX"}
            soup = BeautifulSoup(requests.get(url, headers=header).text)


            try:
                html = await page.evaluate('''() => {
                            return document.querySelector('.main-content').innerHTML;
                        }''')

                parsed_html = BeautifulSoup(html, 'html.parser')

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
                        Config.json_link_name: links[idx+1:]
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

            await page.close()
            await browser.disconnect()
            await browser.close()


