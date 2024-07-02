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
  FIG_NCOLS,
  TICKERS,
  IS_DEBUG,
  SHOW_GRAPHS,
)


def get_tickers():
  return defaultdict(
    bool,
    dict(
      #**COVERED_CALLS,
      **CSEPs,
      #**TEST_SYMBOLS
      #**LTDITM_PUTS,
    )
  )


TEST_SYMBOLS = dict(
  #NVDA=1,
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

  fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
  
  plot_index = 1
  
  for ticker in tickers:
    symbol = ticker.symbol

    try:
      print()
      strategy(symbol, ax)
      plot_index += 1

    except Exception as e:
      print(f'{symbol}: Skipping - {e}')
      if IS_DEBUG:
        traceback.print_exc()
      continue

    if ax.has_data():
      nrow = plot_index if FIG_NCOLS == 1 else (plot_index // 2) + plot_index % FIG_NCOLS
      ax = fig.add_subplot(nrow, FIG_NCOLS, plot_index)

#  for ax in axes.flatten():
#    if not ax.has_data():
#      fig.delaxes(ax)

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

  ncols = FIG_NCOLS
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
#  sell_puts_strategy('NVDA')

  run(sell_short_term_options_strategy)
  #run(sell_LTDITM_puts_strategy)

  # NOTE: YoY ROI generally not worth it (<.05)
#  run(sell_LTDOTM_calls_strategy)
