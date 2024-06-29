import os
import pickle
import pandas as pd
import requests
import math
import matplotlib.pyplot as plt
import traceback
import yfinance as yf

from collections import defaultdict
from datetime import datetime

from analysis.options import (
  find_worthy_short_term_contracts, 
  find_worthy_long_term_contracts,
  find_worthy_contracts,
)
from constants import (
  FIG_WIDTH,
  FIG_HEIGHT,
  TICKERS,
  IS_DEBUG,
  SHOW_GRAPHS,
  NCOLS,
)


def get_tickers():
  return defaultdict(
    bool,
    dict(
      #**COVERED_CALLS,
      #**CSEPs,
      #**TEST_SYMBOLS
      **LTDITM_PUTS,
    )
  )


TEST_SYMBOLS = dict(
  MDB=1,
#  DDOG=1,
#  OKTA=1,
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
  ABNB=1,
  AMZN=1,
  CRM=1,
  CRWD=1,
  GOOG=1,
  META=1,
  GME=1,
  MSFT=1,
  MSTR=1,
  NVDA=1,
  SHOP=1,
  SQ=1,
  TSLA=1,
  TSM=1,
  TXN=1,
)

LTDITM_PUTS = dict(
  MDB=1,  # cc
  SNAP=1,  # cc
  MSTR=1,
  AMZN=1,
  TSLA=1,
  TSM=1,
  TXN=1,
  NVDA=1,
)

SHOW_TICKERS = get_tickers()


def run(strategy=None):
  assert strategy, 'Must provide strategy to run.'

  tickers = sorted([ticker for ticker in TICKERS if SHOW_TICKERS[ticker.symbol] == 1], key=lambda t: t.symbol)

  # add some extra rows for visibility on iPad
  ncols = NCOLS
  nrows = min(max(math.ceil(len(tickers) / ncols), 2), 4)
  fig, axes = plt.subplots(nrows, ncols, figsize=(FIG_WIDTH, FIG_HEIGHT))
  
  plot_index = 0
  
  for ticker in tickers:
    symbol = ticker.symbol
    if plot_index >= ncols * nrows:
      print(f'{symbol}: Plot space maximum reached. Proceeding to graph..')
      break

    row_index = plot_index // 2
    col_index = plot_index % 2

    if ncols == 1:
      ax = axes[plot_index]
    else:
      ax = axes[row_index, col_index]

    try:
      print()
      strategy(symbol, ax)
      plot_index += 1

    except Exception as e:
      print(f'{symbol}: Skipping - {e}')
      if IS_DEBUG:
        traceback.print_exc()
      continue

  for ax in axes.flatten():
    if not ax.has_data():
      fig.delaxes(ax)

  num_axes = len(fig.get_axes())
    
  if SHOW_GRAPHS:
    print('Rendering plot in Output tab...')
    plt.tight_layout()
    fig.subplots_adjust()
    plt.show()


def sell_short_term_options_strategy(symbol, ax):
  if symbol in COVERED_CALLS:
    option_type = 'call'
  elif symbol in CSEPs:
    option_type = 'put'
  else:
    raise ValueError(f'Unclassified symbol: {symbol}')

  find_worthy_short_term_contracts(symbol, option_type, ax)


def sell_LTDITM_puts_strategy(symbol, ax):
  # Look at far away deep ITM Puts.
  find_worthy_long_term_contracts(symbol, 'put', ax)


def sell_LTDOTM_calls_strategy(symbol, ax):
  find_worthy_long_term_contracts(symbol, 'call', ax)


def sell_puts_strategy(symbol):

  ncols = NCOLS
  nrows = 2
  fig, axes = plt.subplots(nrows, ncols, figsize=(FIG_WIDTH, FIG_HEIGHT))
  
  find_worthy_contracts(symbol, 'put', axes)

  for ax in axes.flatten():
    if not ax.has_data():
      fig.delaxes(ax)

  num_axes = len(fig.get_axes())
    
  if SHOW_GRAPHS:
    print('Rendering plot in Output tab...')
    plt.tight_layout()
    fig.subplots_adjust()
    plt.show()


if __name__ == '__main__':
  sell_puts_strategy('NVDA')

#  run(sell_short_term_options_strategy)
  #run(sell_LTDITM_puts_strategy)

  # NOTE: YoY ROI generally not worth it (<.05)
#  run(sell_LTDOTM_calls_strategy)

