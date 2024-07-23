import os
import pytest

import config

from analysis import strategy as Strategy
from graphing import FigureManager
from main import scan, deep_dive_puts


class TestMain:

  @pytest.fixture
  def figman(self):
    return FigureManager()

  @pytest.fixture
  def tickers(self):
    return ('NVDA',)

  def test_scan_success(self, tickers, figman):
    strat = Strategy.sell_intraquarter_derivatives
    scan(strat, tickers, figman)
    figman.render()
  
  def test_scan_move_threshold_error(self, figman):
    strat = Strategy.sell_intraquarter_derivatives
    tickers = ['MDB']
    with pytest.raises(ValueError):
      scan(strat, tickers, figman)

  def test_deep_dive_puts_success(self, tickers, figman):
    strat = deep_dive_puts
    strat(tickers, figman)
    figman.render()
