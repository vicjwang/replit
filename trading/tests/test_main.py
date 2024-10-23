import os
import pytest

import config

from strategy.builds import SellSimplePutCreditSpreadBuild, SellSimplePutBuild
from runners import Scanner, PutDiver

from graphing import FigureManager

from constants import SIDE_SHORT


class TestMain:

  @pytest.fixture
  def figman(self):
    return FigureManager()

  @pytest.fixture
  def tickers(self):
    return ['DDOG']

  def test_scan_success(self, tickers, figman):
    build = SellSimplePutCreditSpreadBuild
    scanner = Scanner(build, figman, win_proba=config.MY_WIN_PROBA, symbols=tickers)
    scanner.run()
    figman.render()

  @pytest.mark.skip()
  def test_deep_dive_puts_success(self, tickers, figman):
    build = SellSimplePutBuild
    runner = PutDiver(build, figman, tickers)
    runner.run(side=SIDE_SHORT)  # FIXME: vjw
    figman.render()
