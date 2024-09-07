import json
import numpy as np
import pandas as pd
import yfinance as yf
import requests
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from scipy.optimize import nnls

yesterday = date.today() + timedelta(days=-1)

train_start = (yesterday - relativedelta(months=5)).isoformat()
train_end = yesterday.isoformat()

available_cedears_list = ['AAPL', 'ABBV', 'AMD', 'ADBE', 'AMZN', 'BA', 'BAC', 'BB', 'BRK-B', 'C', 'CAT', 'CVX', 'COST', 'DIS', 'EBAY', 'FB', 'GE', 'GOLD', 'GOOGL', 'GS', 'INTC', 'JNJ',
                          'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT', 'NFLX', 'NVDA', 'PFE', 'PEP', 'PG', 'PYPL', 'QCOM', 'SBUX', 'SONY', 'SPOT', 'TRIP', 'TSLA', 'TWTR', 'UGP', 'V', 'VZ', 'WFC', 'WMT', 'X', 'XOM']

components = yf.download(
    tickers=available_cedears_list,
    start=train_start,
    end=train_end,
    interval="1d",
    group_by="column",
    auto_adjust=True,
    prepost=False,
    threads=True,
    progress=False
)['Close']

df = components.copy()
df.dropna(inplace=True)

df['Actual Close'] = yf.download(
    tickers="SSO",  # SP500 ETF X2
    start=train_start,
    end=train_end,
    interval="1d",
    group_by="column",
    auto_adjust=True,
    prepost=False,
    threads=True,
    progress=False
)['Close']

trainX = df.drop('Actual Close', axis=1)
trainY = df['Actual Close']

# Obtain coeffs from NNLS training


def get_portfolio_allocation(trainX, trainY):
    result = nnls(trainX, trainY, maxiter=10000)

    leverage_factor = sum(result[0])
    weights = result[0] / leverage_factor
    weights = dict(zip(trainX.columns, weights))

    return leverage_factor, weights


leverage_factor, weights = get_portfolio_allocation(trainX, trainY)

# Corrijo los nombres para poder operar sus cedears
weights['BA.C'] = weights.pop('BAC')
weights['BRKB'] = weights.pop('BRK-B')
weights['DISN'] = weights.pop('DIS')

# removes 0 weighted stocks
portfolio_json = {x: y for x, y in weights.items() if y != 0}

with open('portfolio.json', 'w') as fp:
    json.dump(portfolio_json, fp)
