import os
import pytest

from constants import FROZEN_TEST_DATE
from analysis import strategy as Strategy
from graphing import FigureManager
from main import scan, deep_dive_puts


class TestMain:

  @pytest.fixture
  def figman(self):
    return FigureManager()

  @pytest.fixture
  def tickers(self):
    return ['MDB', 'NVDA']

  @pytest.mark.freeze_time(FROZEN_TEST_DATE)
  def test_scan(self, tickers, figman):
    strat = Strategy.sell_intraquarter_derivatives
    scan(strat, tickers, figman)
    figman.render()

  @pytest.mark.freeze_time(FROZEN_TEST_DATE)
  def test_deep_dive_puts(self, tickers, figman):
    strat = deep_dive_puts
    strat(tickers, figman)
    figman.render()
