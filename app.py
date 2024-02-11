import requests
import json
import os
from flask import send_from_directory
from collections import Counter
from datetime import datetime
from flask import Flask, render_template

class DataAPI:
    url = 'https://etmarketsapis.indiatimes.com/ET_Stats/gainers?pagesize=10&exchange=nse&pageno=1&sort={long}&sortby=percentchange&sortorder=desc&marketcap=largecap&duration={short}'
    ranges = {'1d': 'intraday', '1w': '1week', '1m': '1month', '3m': '3month'}

    def __init__(self, range):
        self.url = self.url.format(long=self.ranges[range], short=range)

    def get_result(self):
        response = requests.request("GET", self.url)
        data = json.loads(response.content)
        self.result = data
        return data['searchresult']

app = Flask(__name__)

@app.route('/')
def index():
    stocks_1d = DataAPI('1d').get_result()
    stocks_1w = DataAPI('1w').get_result()
    stocks_1m = DataAPI('1m').get_result()
    stocks_3m = DataAPI('3m').get_result()

    company_names = [stock['companyShortName'] for stock in stocks_1d]
    company_names.extend(stock['companyShortName'] for stock in stocks_1w)
    company_names.extend(stock['companyShortName'] for stock in stocks_1m)
    company_names.extend(stock['companyShortName'] for stock in stocks_3m)

    company_counts = Counter(company_names)

    company_scores = {}
    for company, count in company_counts.items():
        score = ''
        if count >= 2:
            if company in [stock['companyShortName'] for stock in stocks_1d]:
                score += '1'
            else:
                score += '0'
            if company in [stock['companyShortName'] for stock in stocks_1w]:
                score += '1'
            else:
                score += '0'
            if company in [stock['companyShortName'] for stock in stocks_1m]:
                score += '1'
            else:
                score += '0'
            if company in [stock['companyShortName'] for stock in stocks_3m]:
                score += '1'
            else:
                score += '0'
            company_scores[company] = score

    company_scores = dict(sorted(company_scores.items(), key=lambda item: item[1], reverse=True))

    current_date = datetime.now().strftime("%d-%m-%Y")
    return render_template(
        'index.html',
                           stocks_1d=stocks_1d,
                           stocks_1w=stocks_1w,
                           stocks_1m=stocks_1m,
                           stocks_3m=stocks_3m,
                           current_date=current_date,
                           company_counts=company_counts,
                           company_scores=company_scores,
                        )

if __name__ == '__main__':
    app.run(debug=True)