import requests
import json
import os
from collections import Counter
from datetime import datetime, timedelta
from flask import Flask, render_template, send_from_directory, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CONNECTION_STRING')
db = SQLAlchemy(app)

class StockData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    duration = db.Column(db.String(10))
    data = db.Column(db.JSON)

    def __repr__(self):
        return f"<StockData for {self.date} - Duration: {self.duration}>"


class CompanyScoreData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    data = db.Column(db.JSON)

    def __repr__(self):
        return f"<CompanyScoreData for {self.date}>"


class DataAPI:
    url = 'https://etmarketsapis.indiatimes.com/ET_Stats/gainers?pagesize=10&exchange=nse&pageno=1&sort={long}&sortby=percentchange&sortorder=desc&marketcap=largecap&duration={short}'
    ranges = {'1d': 'intraday', '1w': '1week', '1m': '1month', '3m': '3month'}

    def __init__(self, range):
        self.range = range
        self.url = self.url.format(long=self.ranges[range], short=range)

    def get_result(self):
        response = requests.request("GET", self.url)
        data = json.loads(response.content)

        filtered_data = []
        for full_stock in data['searchresult']:
            stock = {}
            stock['company'] = full_stock['companyShortName']
            stock['change'] = full_stock['percentChange']
            filtered_data.append(stock)

        stock_data = {'date': datetime.now().date(), 'duration': self.range, 'data': filtered_data}
        new_stock_data = StockData(**stock_data)
        db.session.add(new_stock_data)
        db.session.commit()

        return filtered_data


@app.route('/fetch')
def fetch():
    stocks_1d = DataAPI('1d').get_result()
    stocks_1w = DataAPI('1w').get_result()
    stocks_1m = DataAPI('1m').get_result()
    stocks_3m = DataAPI('3m').get_result()

    company_names = [stock['company'] for stock in stocks_1d]
    company_names.extend(stock['company'] for stock in stocks_1w)
    company_names.extend(stock['company'] for stock in stocks_1m)
    company_names.extend(stock['company'] for stock in stocks_3m)

    company_counts = Counter(company_names)

    company_scores = {}
    for company, count in company_counts.items():
        score = ''
        if count >= 2:
            if company in [stock['company'] for stock in stocks_1d]:
                score += '1'
            else:
                score += '0'
            if company in [stock['company'] for stock in stocks_1w]:
                score += '1'
            else:
                score += '0'
            if company in [stock['company'] for stock in stocks_1m]:
                score += '1'
            else:
                score += '0'
            if company in [stock['company'] for stock in stocks_3m]:
                score += '1'
            else:
                score += '0'
            company_scores[company] = {'score': score, 'frequency': count}

    score_data = {'date': datetime.now().date(), 'data': company_scores}
    new_score_data = CompanyScoreData(**score_data)
    db.session.add(new_score_data)
    db.session.commit()

    return "Success", 201


@app.route('/')
def index():
    offset = int(request.args.get('offset', 0))
    target_date = datetime.now().date() - timedelta(days=offset)

    try:
        stocks_1d = StockData.query.filter_by(date=target_date, duration='1d').first().data
        stocks_1w = StockData.query.filter_by(date=target_date, duration='1w').first().data
        stocks_1m = StockData.query.filter_by(date=target_date, duration='1m').first().data
        stocks_3m = StockData.query.filter_by(date=target_date, duration='3m').first().data

        company_scores = CompanyScoreData.query.filter_by(date=target_date).first().data
    except:
        return "<h1>Data Not Found</h1>", 404

    company_scores = dict(sorted(company_scores.items(), key=lambda item: (item[1]['frequency'], item[1]['score']), reverse=True))

    current_date = target_date.strftime("%d-%m-%Y")
    return render_template(
        'index.html',
                           stocks_1d=stocks_1d,
                           stocks_1w=stocks_1w,
                           stocks_1m=stocks_1m,
                           stocks_3m=stocks_3m,
                           current_date=current_date,
                           company_scores=company_scores,
                        )

if __name__ == '__main__':
    app.run(debug=True)