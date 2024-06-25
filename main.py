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

from analysis.options import show_worthy_contracts
from constants import (
  FIG_WIDTH,
  FIG_HEIGHT,
  TICKERS,
  IS_DEBUG,
  SHOW_GRAPHS
)


def get_tickers():
  return defaultdict(
    bool,
    dict(
      #**COVERED_CALLS,
      #**CSEPs,
      **TEST_SYMBOLS
    )
  )


TEST_SYMBOLS = dict(
  DDOG=1,
  DIS=1,
)


# Global parameters.
NCOLS = 2


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

SHOW_TICKERS = get_tickers()


def setup_figure(num_rows, num_cols):
  fig, axes = plt.subplots(num_rows, num_cols, figsize=(FIG_WIDTH, FIG_HEIGHT))
  return fig, axes


def run_sell_options_strategy():

  tickers = sorted([ticker for ticker in TICKERS if SHOW_TICKERS[ticker.symbol] == 1], key=lambda t: t.symbol)

  # add some extra rows for visibility on iPad
  ncols = NCOLS
  nrows = min(max(math.ceil(len(tickers) / ncols), 2), 4)
  fig, axes = setup_figure(nrows, ncols)
  
  plot_index = 0
  
  for ticker in tickers:
    print()
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


if __name__ == '__main__':
  run_sell_options_strategy()


