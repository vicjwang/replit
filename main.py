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
      **COVERED_CALLS,
      **CSEPS,
      #**TEST_SYMBOLS
      #**LTDITM_PUTS,
    )
  )

  ret = sorted([ticker for ticker in TICKERS if selected_tickers[ticker.symbol] == 1], key=lambda t: t.symbol)
  return ret



TEST_SYMBOLS = dict(
  NVDA=1,
  CRWD=1,
  MSTR=1,
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

  print('Rendering plot in Output tab...')
  plt.tight_layout()
  fig.subplots_adjust()
  plt.show()


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

  render_many(strategy.sell_short_term_derivatives)
  #render_many(strategy.sell_LTDITM_puts)

