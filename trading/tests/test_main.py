import os
import pytest

import config

from strategy.builds import SellSimplePutCreditSpreadBuild, SellSimplePutBuild
from runners import Scanner, PutDiver

from graphing import FigureManager
from main import scan, deep_dive_puts, deep_dive_calls

from constants import SIDE_SHORT


class TestMain:

  @pytest.fixture
  def figman(self):
    return FigureManager()

  @pytest.fixture
  def tickers(self):
    return ('NVDA',)

  def test_scan_success(self, tickers, figman):
    build = SellSimplePutCreditSpreadBuild
    scanner = Scanner(build, figman, win_proba=config.MY_WIN_PROBA, symbols=tickers)
    scanner.run()
    figman.render()

  def test_deep_dive_puts_success(self, tickers, figman):
    build = SellSimplePutBuild
    runner = PutDiver(build, figman, tickers)
    runner.run(side=SIDE_SHORT)  # FIXME: vjw
    figman.render()

  
  @pytest.mark.skip()
  def test_scan_move_threshold_error(self, figman):
    strat = Runners.sell_intraquarter_derivatives
    tickers = ['MDB']
    with pytest.raises(ValueError):
      scan(strat, tickers, figman)


  @pytest.mark.skip()
  def test_deep_dive_calls_success(self, tickers, figman):
    strat = deep_dive_calls
    strat(tickers, figman)
    figman.render()

