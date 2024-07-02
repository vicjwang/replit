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
  find_worthy_contracts,
)
from analysis import strategy
from constants import (
  COVERED_CALLS,
  CSEPS,
  LTDITM_PUTS,
  FIG_WIDTH,
  FIG_HEIGHT,
  FIG_NCOLS,
  IS_DEBUG,
  SHOW_GRAPHS,
  TICKERS,
)


def get_tickers():
  selected_tickers = defaultdict(
    bool,
    dict(
      #**COVERED_CALLS,
      #**CSEPS,
      **TEST_SYMBOLS
      #**LTDITM_PUTS,
    )
  )

  ret = sorted([ticker for ticker in TICKERS if selected_tickers[ticker.symbol] == 1], key=lambda t: t.symbol)
  return ret


TEST_SYMBOLS = dict(
  NVDA=1,
  MDB=1,
#  CRWD=1,
#  MSTR=1,
#  SNAP=1,
#  TWLO=1,
)


def render_many(strategy):
  # Run strategy across many tickers.

  strats = []

  tickers = get_tickers()
  for ticker in tickers:
    symbol = ticker.symbol

    try:
      strat = strategy(symbol)
      strats.append(strat)

    except Exception as e:
      print(f'{symbol}: Skipping - {e}')
      if IS_DEBUG:
        traceback.print_exc()
      continue

  if not SHOW_GRAPHS or not strats:
    raise RuntimeError('No graphs to render.')

  nrows = math.ceil(len(strats) / FIG_NCOLS)
  ncols = FIG_NCOLS
  fig, axes = plt.subplots(nrows, ncols, figsize=(FIG_WIDTH, FIG_HEIGHT))
  for i, strat in enumerate(strats):

    if nrows == 1 or ncols == 1:
      ax = axes[i]
    else:
      row_index = i // 2
      col_index = i % 2
      ax = axes[row_index, col_index]

    print()
    strat.pprint()
    strat.graph_roi_vs_expiry(ax)

  fig.subplots_adjust()


def render_one(strategy):
  # Run strategy on one ticker.

  ncols = FIG_NCOLS
  nrows = 3
  fig, axes = plt.subplots(nrows, ncols, figsize=(FIG_WIDTH, FIG_HEIGHT))

  i = 0
  for zscore in [1, 0, -1]:
    for option_type in ['call', 'put']:

      if nrows == 1 or ncols == 1:
        ax = axes[i]
      else:
        row_index = i // 2
        col_index = i % 2
        ax = axes[row_index, col_index]

      strategy.prepare_graph_data(option_type, zscore)
      strategy.graph_roi_vs_expiry(ax, zscore)
      i += 1

  fig.subplots_adjust()


if __name__ == '__main__':

#  render_many(strategy.sell_short_term_derivatives)
#  render_many(strategy.sell_LTDITM_puts)

#  render_one(strategy.sell_derivatives('NVDA'))
  #render_one(strategy.sell_derivatives('MDB'))
  render_one(strategy.sell_derivatives('MSTR'))

  if SHOW_GRAPHS:
    print('Rendering plot in Output tab...')
    plt.tight_layout()
    plt.show()
  
