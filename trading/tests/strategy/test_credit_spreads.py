import pandas as pd
from unittest.mock import patch

import config

from datetime import datetime

from constants import DATE_FORMAT
from strategy.credit_spreads import CreditSpreadStrategy


class TestCreditSpreadStrategy:

  def test_make_snapshot(self, snapshot):
    symbol = 'MDB'
    strat = CreditSpreadStrategy(symbol, side='short')
    result = strat.make_snapshot('put', 0.15).df.to_csv()

    assert result == snapshot
