import argparse
import sys
import traceback

import config

from collections import defaultdict
from joblib import Parallel, delayed

from analysis import strategy as Strategy
from constants import (
  COVERED_CALLS,
  WATCHLIST,
  SIDE_SHORT,
  STOCKS,
)
from graphing import FigureManager

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


def scan(snapshot_fn, tickers, figman, win_proba=config.MY_WIN_PROBA):
  # Scan across many stocks.
  # One figure will show same strategy across multiple stocks.

  def process(stock):
    symbol = stock.symbol

    try:
      return snapshot_fn(symbol, win_proba=win_proba)

    except Exception as e:
      print(strformat(symbol, f"Skipping - {e}"))
      if config.IS_DEBUG:
        traceback.print_exc()
        raise e

  figman.add_empty_figure(snapshot_fn.__name__)

  stocks = get_stocks(tickers)

  snapshots = Parallel(n_jobs=config.NUM_PARALLEL_JOBS)(delayed(process)(stock) for stock in stocks)

  for snapshot in snapshots:
    if snapshot:
      figman.add_graph_as_ax(snapshot.graph_roi_vs_expiry)
      print(strformat(snapshot.symbol, f"Adding subplot (WORTHY_MIN_BID={config.WORTHY_MIN_BID}, WORTHY_MIN_ROI={config.WORTHY_MIN_ROI})\n \"{snapshot.title}\"\n"))


def deep_dive_puts(tickers, figman):
  # Run strategy on one stock.
  # One figure will show same strategy for one stock.

  stocks = get_stocks(tickers)
  for stock in stocks:
    symbol = stock.symbol
    strat = Strategy.DerivativeStrategyBase(symbol, side=SIDE_SHORT)
    print(strat)
  
    sig_levels = [0.15, 0.10, 0.05, 0.01]
    deep_dive(strat, 'put', sig_levels, figman)


def deep_dive_calls(tickers, figman):
  stocks = get_stocks(tickers)
  for stock in stocks:
    symbol = stock.symbol
    if symbol not in COVERED_CALLS:
      continue

    strat = Strategy.DerivativeStrategyBase(symbol, side=SIDE_SHORT)
    sig_levels = [0.5, 0.85, 0.90, 0.95, 0.975, 0.99]
    deep_dive(strat, 'call', sig_levels, figman)


def deep_dive(strategy, option_type, sig_levels, figman):

  symbol = strategy.symbol
  figman.add_empty_figure(strformat(symbol, option_type))

  for sig_level in sig_levels:
    try:
      snapshot = strategy.build_snapshot(option_type, sig_level)
      figman.add_graph_as_ax(snapshot.graph_roi_vs_expiry)
      print(strformat(symbol, f"Adding subplot (WORTHY_MIN_BID={config.WORTHY_MIN_BID}, WORTHY_MIN_ROI={config.WORTHY_MIN_ROI})\n \"{snapshot.title}\""))

    except Exception as e:
      print(strformat(symbol, f"Skipping - {e}"))
      if config.IS_DEBUG:
        traceback.print_exc()
        raise e
      else:
        continue
  print()


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('command')
  parser.add_argument('-t', '--tickers')
  parser.add_argument('-s', '--strategy')
  parser.add_argument('-p', '--proba')

  args = parser.parse_args()

  cmd = args.command
  tickers = args.tickers.upper().split(',') if args.tickers else None
  strategy_input = args.strategy
  win_proba = float(args.proba) if args.proba else config.MY_WIN_PROBA

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
      scan(strat, tickers, figman, win_proba=win_proba)
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
