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
from analysis.strategy import DerivativeStrategy
from constants import (
  FIG_WIDTH,
  FIG_HEIGHT,
  FIG_NCOLS,
  IS_DEBUG,
  MIN_EXPIRY_DATESTR,
  MY_WIN_PROBA,
  SHOW_GRAPHS,
  SIDE_SHORT,
  TICKERS,
  WIN_PROBA_ZSCORE,
)


def get_tickers():
  selected_tickers = defaultdict(
    bool,
    dict(
      **COVERED_CALLS,
      #**CSEPs,
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


def sell_short_term_derivatives(symbol):
  if symbol in COVERED_CALLS:
    option_type = 'call'
  elif symbol in CSEPs:
    option_type = 'put'
  else:
    raise ValueError(f'Unclassified symbol: {symbol}')

  side = SIDE_SHORT

  deriv_strat = DerivativeStrategy(symbol, option_type=option_type, side=side)
  price_model = deriv_strat.get_price_model()

  latest_price = price_model.get_latest_price()
  latest_change = price_model.get_latest_change()

  zscore = WIN_PROBA_ZSCORE[side][option_type][MY_WIN_PROBA]

  if (option_type == 'call' and latest_change < 0) or (option_type == 'put' and latest_change > 0):
    raise ValueError(f'Skipping - {symbol} {option_type} move threshold not met. ${latest_price}, {round(latest_change * 100, 2)}%')

  next_earnings_date = price_model.get_next_earnings_date()

  deriv_strat.prepare_graph_data(zscore, end_date=next_earnings_date)
  return deriv_strat


def sell_LTDITM_puts(symbol):
  # Look at far away deep ITM Puts.
  side = SIDE_SHORT
  option_type = 'put'
  zscore = WIN_PROBA_ZSCORE[side][option_type][MY_WIN_PROBA]

  deriv_strat = DerivativeStrategy(symbol, option_type=option_type, side=side)
  deriv_strat.prepare_graph_data(zscore, start_date=MIN_EXPIRY_DATESTR)
  return deriv_strat


def sell_LTDOTM_calls(symbol):
  # NOTE: YoY ROI generally not worth it (<.05)
  side = SIDE_SHORT
  option_type = 'call'
  zscore = WIN_PROBA_ZSCORE[side][option_type][MY_WIN_PROBA]

  deriv_strat = DerivativeStrategy(symbol, option_type=option_type, side=side)
  deriv_strat.prepare_graph_data(zscore, start_date=MIN_EXPIRY_DATESTR)
  return deriv_strat


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

#  render_many(sell_short_term_derivatives)
  render_many(sell_LTDITM_puts)

