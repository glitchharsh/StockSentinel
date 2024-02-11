import requests
import pprint
import json

class DataAPI:
    url = 'https://etmarketsapis.indiatimes.com/ET_Stats/gainers?pagesize=10&exchange=nse&pageno=1&sort={long}&sortby=percentchange&sortorder=desc&marketcap=largecap&duration={short}'
    ranges = {'1d': 'intraday', '1w': '1week', '1m': '1month', '3m': '3month'}

    def __init__(self, range):
        self.url = self.url.format(long=self.ranges[range], short=range)

    def get_result(self):
        response = requests.request("GET", self.url)
        data = json.loads(response.content)
        self.result = data
        self.stocks = data['searchresult']