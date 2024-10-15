import os
import pytest

import config

from datetime import datetime
from unittest.mock import patch

from strategy.builds import SellSimplePutCreditSpreadBuild, SellSimplePutBuild

from constants import SIDE_SHORT


@patch('config.NOW', datetime(2024, 10, 17))
class TestSellSimplePutBuild:

  def test_validate_move_threshold_success(self):
    tickers = ('MDB',)
    for ticker in tickers:
      SellSimplePutBuild(ticker, config.MY_WIN_PROBA).create_snapshot()
      assert True

  @patch('config.MIN_ZSCORE_THRESHOLD', 0.85)
  def test_move_threshold_error(self):
    tickers = ('DIS', 'AAPL', 'CRWD', 'TSM')
    for ticker in tickers:
      with pytest.raises(ValueError):
        SellSimplePutBuild(ticker, config.MY_WIN_PROBA).create_snapshot()
