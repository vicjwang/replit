import argparse
import sys
import traceback

import config

from strategy.builds import SellSimplePutCreditSpreadBuild, SellSimplePutBuild

from collections import defaultdict
from joblib import Parallel, delayed


from constants import (
  COVERED_CALLS,
  WATCHLIST,
  SIDE_SHORT,
  STOCKS,
)
from graphing import FigureManager

from utils import strformat

from runners import Scanner, PutDiver


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
  runner = None

  if cmd == 'scan':
    build = SellSimplePutCreditSpreadBuild
    runner = Scanner(build, figman, tickers, win_proba=win_proba)
    runner.run()

  elif cmd == 'dd':
    build = SellSimplePutBuild
    runner = PutDiver(build, figman, tickers)
    runner.run(side=SIDE_SHORT)  # FIXME? vjw

  else:
    print(f"Invalid command - either 'scan' or 'dd'")
    sys.exit(1)

  figman.render()
