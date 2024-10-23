import pandas as pd

import config

from datetime import datetime
from unittest.mock import patch

from constants import DATE_FORMAT
from strategy.base import DerivativeStrategyBase


class TestDerivativeStrategyBase:

  @patch('config.WORTHY_MIN_ROI', 0.2)
  def test_make_snapshot(self, snapshot):
    symbol = 'MDB'
    strat = DerivativeStrategyBase(symbol, side='short')
    result = strat.make_snapshot('put', 0.15).df.to_csv()

    assert result == snapshot
