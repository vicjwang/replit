import argparse
import sys
import traceback

import config

from constants import (
  SIDE_SHORT, WATCHLIST
)
from graphing import FigureManager
from runners import Scanner, PutDiver
from strategy.builds import SellSimplePutCreditSpreadBuild, SellSimplePutBuild


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('command')
  parser.add_argument('-t', '--tickers')
  parser.add_argument('-s', '--strategy')
  parser.add_argument('-p', '--proba')

  args = parser.parse_args()

  cmd = args.command
  tickers = args.tickers.upper().split(',') if args.tickers else WATCHLIST.keys()
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
