import argparse
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
  WATCHLIST,
  FIG_WIDTH,
  FIG_HEIGHT,
  FIG_NCOLS,
  IS_DEBUG,
  SIDE_SHORT,
  SHOW_GRAPHS,
  STOCKS,
  WORTHY_MIN_BID,
  WORTHY_MIN_ROI,
)

from utils import strformat


def get_stocks(tickers=None):
  
  if tickers:
    selected = defaultdict(bool, dict(zip(tickers, [1]*len(tickers))))
  else:
    selected = defaultdict(
      bool,
      dict(
        **COVERED_CALLS,
        **WATCHLIST,
      )
    )

  ret = sorted([stock for stock in STOCKS if selected[stock.symbol] == 1], key=lambda t: t.symbol)
  return ret


def scan(snapshot_fn, tickers, figman):
  # Scan across many stocks.
  # One figure will show same strategy across multiple stocks.
  figman.add_empty_figure(strat.__name__)

  stocks = get_stocks(tickers)

  for stock in stocks:
    symbol = stock.symbol

    try:
      snapshot = snapshot_fn(symbol)

    except Exception as e:
      print(strformat(symbol, f"Skipping - {e}"))
      if IS_DEBUG:
        traceback.print_exc()
      continue

    figman.add_graph_as_ax(snapshot.graph_roi_vs_expiry)
    print(strformat(symbol, f"Adding subplot (WORTHY_MIN_BID={WORTHY_MIN_BID}, WORTHY_MIN_ROI={WORTHY_MIN_ROI})\n \"{snapshot.title}\"\n"))


def deep_dive_puts(tickers, figman):
  # Run strategy on one stock.
  # One figure will show same strategy for one stock.

  stocks = get_stocks(tickers)
  for stock in stocks:
    symbol = stock.symbol
    strat = Strategy.DerivativeStrategyBase(symbol, side=SIDE_SHORT)
    print(strat)

    zscores = [-1, -1.28, -1.645, -2.33]
    deep_dive(strat, 'put', zscores)


def deep_dive_calls(tickers, figman):
  stocks = get_stocks(tickers)
  for stock in stocks:
    symbol = stock.symbol
    if symbol not in COVERED_CALLS:
      continue

    zscores = [0, 1, 1.28, 1.645, 2.33]
    deep_dive(symbol, 'call', zscores)


def deep_dive(strategy, option_type, zscores):

  symbol = strategy.symbol
  figman.add_empty_figure(strformat(symbol, option_type))

  for zscore in zscores:
    try:
      snapshot = strategy.build_snapshot(option_type, zscore=zscore)
      figman.add_graph_as_ax(snapshot.graph_roi_vs_expiry)
      print(strformat(symbol, f"Adding subplot (WORTHY_MIN_BID={WORTHY_MIN_BID}, WORTHY_MIN_ROI={WORTHY_MIN_ROI})\n \"{snapshot.title}\""))

    except Exception as e:
      print(strformat(symbol, f"Skipping - {e}"))
      if IS_DEBUG:
        traceback.print_exc()
      continue
  print()


class FigureManager:
  
  def __init__(self):
    self.figures = OrderedDict()
    self.current_figure = None

  def add_graph_as_ax(self, graph_fn, *args, **kwargs):
    self.current_figure.append((graph_fn, args, kwargs))

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
        graph_fn, args, kwargs = graph

        if nrows == 1 or ncols == 1:
          ax = axes[i]
        else:
          row_index = i // 2
          col_index = i % 2
          ax = axes[row_index, col_index]

        print()
        graph_fn(ax, *args, **kwargs)

      fig.subplots_adjust()
      plt.tight_layout()

    print('Rendering in Output tab...')
    plt.show()


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('command')
  parser.add_argument('-t', '--tickers')
  parser.add_argument('-s', '--strategy')

  args = parser.parse_args()

  cmd = args.command
  tickers = args.tickers.upper().split(',') if args.tickers else None
  strategy_input = args.strategy

  figman = FigureManager()

  # Scan across stocks with strategies.
  if cmd == 'scan':
    scan_strats = [
      Strategy.sell_intraquarter_derivatives,
      Strategy.sell_LTDITM_puts,
    ]

    if strategy_input is None:
      for strat in scan_strats:
        scan(strat, tickers, figman)
    elif strategy_input.isdigit():
      strat = scan_strats[int(strategy_input)]
      scan(strat, tickers, figman)
    else:
      print(f"Invalid strategy:", ' '.join([f"{i}={strat.__name__}" for i, strat in enumerate(scan_strats)]))
      sys.exit(1)

  elif cmd == 'dd':
    strats = [
      deep_dive_calls,
      deep_dive_puts,
    ]

    if strategy_input is None:
      for strat in strats:
        strat(tickers, figman)
    elif strategy_input.isdigit():
      strat = strats[int(strategy_input)]
      strat(tickers, figman)
    else:
      print(f"Invalid strategy:", ' '.join([f"{i}={strat.__name__}" for i, strat in enumerate(strats)]))
      sys.exit(1)

  else:
    print(f"Invalid command - either 'scan' or 'dd'")
    sys.exit(1)

  figman.render()
