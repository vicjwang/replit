import os
import pickle
import pandas as pd
import requests
import math
import matplotlib.pyplot as plt
import sys
import traceback
import yfinance as yf

from collections import defaultdict, OrderedDict
from datetime import datetime

from analysis import strategy as Strategy
from constants import (
  COVERED_CALLS,
  CSEPS,
  LTDITM_PUTS,
  FIG_WIDTH,
  FIG_HEIGHT,
  FIG_NCOLS,
  IS_DEBUG,
  SIDE_SHORT,
  SHOW_GRAPHS,
  TICKERS,
)


def get_tickers():
  selected_tickers = defaultdict(
    bool,
    dict(
#      **COVERED_CALLS,
      #**CSEPS,
      **DD_SYMBOLS
      #**LTDITM_PUTS,
    )
  )

  ret = sorted([ticker for ticker in TICKERS if selected_tickers[ticker.symbol] == 1], key=lambda t: t.symbol)
  return ret


DD_SYMBOLS = dict(
  NVDA=1,
  TSLA=1,
#  MDB=1,
#  V=1,
#  CRWD=1,
#  MSTR=1,
#  SNAP=1,
#  TWLO=1,
)


def scan(strategy, figman):
  # Scan across many tickers.
  # One figure will show same strategy across multiple tickers.
  figman.add_empty_figure(strat.__name__)

  tickers = get_tickers()
  for ticker in tickers:
    symbol = ticker.symbol

    try:
      instance = strategy(symbol)

    except Exception as e:
      print(f"{symbol}: Skipping - {e}")
      if IS_DEBUG:
        traceback.print_exc()
      continue

    figman.add_graph_as_ax(instance.graph_roi_vs_expiry)


def put_deep_dives(figman):
  # Run strategy on one ticker.
  # One figure will show same strategy for one ticker.

  tickers = get_tickers()
  for ticker in tickers:
    symbol = ticker.symbol
    if symbol not in CSEPS:
      continue

    zscores = [-1, -1.28, -1.645, -2.33]
    deep_dive(symbol, 'put', zscores)


def call_deep_dives(figman):
  tickers = get_tickers()
  for ticker in tickers:
    symbol = ticker.symbol
    if symbol not in COVERED_CALLS:
      continue

    zscores = [0, 1, 1.28, 1.645, 2.33]
    deep_dive(symbol, 'call', zscores)


def deep_dive(symbol, option_type, zscores):

  figman.add_empty_figure(f"{symbol}: {option_type}")

  instance = Strategy.DerivativeStrategy(symbol, side=SIDE_SHORT)

  for zscore in zscores:
    try:
      instance.prepare_graph_data(option_type)
      figman.add_graph_as_ax(instance.graph_roi_vs_expiry, zscore)

    except Exception as e:
      print(f"{instance}: Skipping - {e}")
      if IS_DEBUG:
        traceback.print_exc()
      continue


class FigureManager:
  
  def __init__(self):
    self.figures = OrderedDict()
    self.current_figure = None

  def add_graph_as_ax(self, graph_fn, *args):
    self.current_figure.append((graph_fn, args))

  def add_empty_figure(self, title):
    self.figures[title] = []
    self.current_figure = self.figures[title]

  def render(self):
    
    if not SHOW_GRAPHS:
      print(f"No graphs to render (SHOW_GRAPHS={SHOW_GRAPHS}).")
      return

    for fig_title, graphs in self.figures.items():
      if len(graphs) == 0:
        print('Skipping', fig_title, '- no graphs to render.')
        continue
      
      nrows = math.ceil(len(graphs) / FIG_NCOLS)
      ncols = FIG_NCOLS
      fig, axes = plt.subplots(nrows, ncols, figsize=(FIG_WIDTH, FIG_HEIGHT))

      fig.canvas.manager.set_window_title(fig_title)

      for i, graph in enumerate(graphs):
        graph_fn, args = graph

        if nrows == 1 or ncols == 1:
          ax = axes[i]
        else:
          row_index = i // 2
          col_index = i % 2
          ax = axes[row_index, col_index]

        print()
        graph_fn(ax, *args)

      fig.subplots_adjust()
      plt.tight_layout()

    print('Rendering in Output tab...')
    plt.show()


if __name__ == '__main__':

  figman = FigureManager()

  # Scan across tickers with strategies.
  strats = [
    Strategy.sell_intraquarter_derivatives,
#    Strategy.sell_LTDITM_puts,
  ]
  for strat in strats:
    scan(strat, figman)

  #put_deep_dives(figman)
  #call_deep_dives(figman)

  figman.render()
