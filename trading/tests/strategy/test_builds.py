import os
import pytest

import config

from datetime import datetime
from unittest.mock import patch

from strategy.builds import SellSimplePutCreditSpreadBuild, SellSimplePutBuild

from constants import SIDE_SHORT


class TestSellSimplePutBuild:

  def test_validate_move_threshold_success(self):
    tickers = ('MDB', 'NVDA',)
    for ticker in tickers:
      SellSimplePutBuild(ticker, config.MY_WIN_PROBA).create_snapshot()
      assert True

  def test_no_eligible_options_error(self):
    tickers = ('GOOG', 'TSLA')
    for ticker in tickers:
      with pytest.raises(ValueError):
        SellSimplePutBuild(ticker, config.MY_WIN_PROBA).create_snapshot()

  @patch('config.MIN_ZSCORE_THRESHOLD', 0.85)
  def test_move_threshold_error(self):
    tickers = ('SNAP', 'TXN')
    for ticker in tickers:
      with pytest.raises(ValueError):
        SellSimplePutBuild(ticker, config.MY_WIN_PROBA).create_snapshot()
