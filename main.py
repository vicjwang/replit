import argparse
import sys
import traceback

from collections import defaultdict

from analysis import strategy as Strategy
from constants import (
  COVERED_CALLS,
  WATCHLIST,
  IS_DEBUG,
  SIDE_SHORT,
  STOCKS,
  WORTHY_MIN_BID,
  WORTHY_MIN_ROI,
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


def scan(snapshot_fn, tickers, figman):
  # Scan across many stocks.
  # One figure will show same strategy across multiple stocks.
  figman.add_empty_figure(snapshot_fn.__name__)

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
    deep_dive(strat, 'put', zscores, figman)


def deep_dive_calls(tickers, figman):
  stocks = get_stocks(tickers)
  for stock in stocks:
    symbol = stock.symbol
    if symbol not in COVERED_CALLS:
      continue

    zscores = [0, 1, 1.28, 1.645, 2.33]
    deep_dive(symbol, 'call', zscores, figman)


def deep_dive(strategy, option_type, zscores, figman):

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
