import os
import pickle
import pandas as pd
import requests
import matplotlib.pyplot as plt
import traceback

from datetime import datetime

from analyze_options import determine_overpriced_option_contracts, show_worthy_contracts
from collections import defaultdict
#from analyze_fundamentals import graph_historical_valuations
from constants import (
  SHOULD_AVOID_EARNINGS,
  PLT_WIDTH,
  PLT_HEIGHT,
  TICKERS,
)

from utils import printout, get_option_contract_str

import yfinance as yf


SHOW_GRAPH = True
RENDER_FIG = True

TEST_SYMBOL = dict(
  TSM=1,
  #AAPL=1
)

COVERED_CALLS = dict(
  DDOG=1,  # cc
  DIS=1,  # cc
  OKTA=1,  # cc
  MDB=1,  # cc
  SNAP=1,  # cc
  TWLO=1,  # cc
)

CSEPs = dict(
  AAPL=1,
  #ABNB=1,
  #AMZN=1,
  #CRM=1,
  #CRWD=1,

  #GOOG=1,

  #META=1,

  #GME=1,
  #MSFT=1,
  #MSTR=1,
  NVDA=1,
  SHOP=1,
  SQ=1,
  TSLA=1,
  TSM=1,
  TXN=1,
)

SHOW_TICKERS = defaultdict(
  bool,
  dict(
    **COVERED_CALLS,
    **CSEPs,
    #**TEST_SYMBOL
  )
)


START_DATE = '2023-01-01'  # rate cut?
#START_DATE = '2020-04-01' # COVID
EXPIRY_DAYS = None


def cache():
  def decorator(func):
    def wrapper(*args, **kwargs):
      file_name = func.__name__ + '_' + '-'.join(args) + '.pkl'
      if os.path.exists(file_name):
        # If the pickle file exists, load the cached result
        with open(file_name, 'rb') as file:
          result = pickle.load(file)
      else:
        # If the file doesn't exist, call the function and cache the result
        result = func(*args, **kwargs)
        with open(file_name, 'wb') as file:
          pickle.dump(result, file)
      return result
    return wrapper
  return decorator




#@cache
def fetch_raw_pe(symbol, company):
  url = f'https://www.macrotrends.net/stocks/charts/{symbol}/{company}/pe-ratio'
  return fetch_raw_historical(url)


def fetch_raw_pfcf(symbol, company):
  url = f'https://www.macrotrends.net/stocks/charts/{symbol}/{company}/price-fcf'
  return fetch_raw_historical(url)


def fetch_raw_historical(url):

  headers = {
      'User-Agent': (
          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
          '(KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
      )
  }
  resp = requests.get(url, headers=headers)

  data = pd.read_html(resp.text, skiprows=1)
  return data[0]


def graph_historical_pe(symbol, company, start_date=None, ax=None):
  column_names = ['Date', 'Price', 'EPS', 'PE']
  data = fetch_raw_pe(symbol, company)
  data.columns = column_names

  date = data['Date'].apply(pd.to_datetime)
  pe = data['PE'].apply(pd.to_numeric)
  pe_mean = round(pe.mean(), 2)

  print('Last earnings date:', date.iloc[0])
  print('Last earnings PE:', pe.iloc[0])
  print('Historical mean PE:', pe_mean)

  if ax:
    graph_historical(date.tolist(), pe.tolist(), pe_mean, symbol, ax)


def graph_historical(x, y, mean, title, ax):
  ax.set_title(title)
  ax.plot(x, y)
  ax.plot(x, [mean] * len(x), color='r', linestyle='--')


def setup_plots(num_rows, num_cols):
  fig, axes = plt.subplots(num_rows, num_cols, figsize=(PLT_WIDTH, PLT_HEIGHT * 6))
  return fig, axes


def main():

  tickers = sorted([ticker for ticker in TICKERS if SHOW_TICKERS[ticker.symbol] == 1], key=lambda t: t.symbol)

  start_date = START_DATE
  
  fig, axes = setup_plots(len(tickers), 2)

  contracts = []

  for i, ticker in enumerate(tickers):
    printout('#' * 70)
    print(ticker)

    row_i = i // 2
    col_j = i % 2

    if (len(tickers) < 2):
      ax = axes[i]
    else:
      ax = axes[row_i, col_j]
    #fig.add_subplot(len(tickers), 2, i + 1) if fig else None
    if ax:
      ax.set_title(ticker.name)

    next_earnings_date = None
    try:
      next_earnings_date = datetime.strptime(ticker.next_earnings, '%Y-%m-%d')
    except:
      pass

    expiry_days = EXPIRY_DAYS

    if next_earnings_date and SHOULD_AVOID_EARNINGS:
      delta_days = (next_earnings_date - datetime.now()).days
      if delta_days > 1:
        expiry_days = delta_days

    overpriced_contracts = determine_overpriced_option_contracts(ticker.symbol, start_date, ax)

    for contract in overpriced_contracts:
      ticker = contract['root_symbol']
      desc = contract['description']
      last = contract['last']
      annual_roi = contract['annual_roi']
      print(f' {desc} last={last} annual_roi={round(annual_roi, 2)*100}%')

    contracts += overpriced_contracts
    #graph_historical_pe(ticker.symbol, ticker.name, start_date, ax)

    printout()
    printout()

  print(f'Found {len(contracts)} potentially overpriced option contracts:')
  for contract in sorted(contracts, key=lambda c: -c['annual_roi']):
    ticker = contract['root_symbol']
    option_str = get_option_contract_str(contract)
    print(' ', option_str)


  if SHOW_GRAPH:
    printout('Rendering plot in Output tab...')
    plt.tight_layout()
    fig.subplots_adjust() 
    plt.show()


def graph_main():

  tickers = sorted([ticker for ticker in TICKERS if SHOW_TICKERS[ticker.symbol] == 1], key=lambda t: t.symbol)

  # add some extra rows for visibility on iPad
  ncols = 2
  fig, axes = setup_plots(5, ncols)

  plot_index = 0
  
  for ticker in tickers:
    symbol = ticker.symbol
    row_index = plot_index // 2
    col_index = plot_index % 2

    if symbol in COVERED_CALLS:
      option_type = 'call'
    elif symbol in CSEPs:
      option_type = 'put'
    else:
      print(f'Unclassified symbol: {symbol}..')
      continue

    try:
      if ncols == 1:
        show_worthy_contracts(symbol, option_type, axes[plot_index])
      else:
        show_worthy_contracts(symbol, option_type, axes[row_index, col_index])
      plot_index += 1

    except Exception as e:
      print(f'Skipping to graph {symbol}: {e}')
      traceback.print_exc()
      continue

  print('Rendering plot in Output tab...')
  plt.tight_layout()
  fig.subplots_adjust(bottom=0.1)
  plt.show()

if __name__ == '__main__':
  #main()
  graph_main()


