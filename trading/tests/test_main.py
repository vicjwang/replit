import os
import pytest

import config

from unittest.mock import Mock, patch

from analysis import strategy as Strategy
from graphing import FigureManager
from main import scan, deep_dive_puts, deep_dive_calls


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
  
  def test_scan_move_threshold_error(self, figman, tickers):
    strat = Strategy.sell_intraquarter_derivatives
    mock_model = Mock()
    mock_model.get_latest_change.return_value = 0
    mock_model.get_daily_stdev.return_value = 0
    with patch('analysis.strategy.DerivativeStrategyBase.get_price_model', return_value=mock_model), pytest.raises(ValueError):
      scan(strat, tickers, figman)

  def test_deep_dive_puts_success(self, tickers, figman):
    strat = deep_dive_puts
    strat(tickers, figman)
    figman.render()

  def test_deep_dive_calls_success(self, tickers, figman):
    strat = deep_dive_calls
    strat(tickers, figman)
    figman.render()

