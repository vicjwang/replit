import pandas as pd
from unittest.mock import patch

import config

from datetime import datetime

from constants import DATE_FORMAT
from strategy.base import DerivativeStrategyBase


SNAPSHOT_CSV_TEMPLATE = 'tests/fixtures/{symbol}-snapshot-{YYYYmmdd}.csv'


class TestDerivativeStrategyBase:
  
  @patch('config.WORTHY_MIN_ROI', 0.2)
  def test_make_snapshot(self):
    symbol = 'MDB'
    strat = DerivativeStrategyBase(symbol, side='short')
    snapshot = strat.make_snapshot('put', 0.15)

    result = snapshot.df
    snapshot_csv = SNAPSHOT_CSV_TEMPLATE.format(symbol=symbol, YYYYmmdd=config.NOW.strftime('%Y%m%d'))
    expected = pd.read_csv(snapshot_csv, parse_dates=['expiration_date'])

    pd.testing.assert_frame_equal(result, expected, check_dtype=False, check_like=True)


if __name__ == '__main__':
  # Usage: 
  # $ ENV=test poetry run python -m tests.test_derivative_strategy

#  symbol = 'MDB'
  symbols = 'OKTA'.split(',')

  for symbol in symbols:
    strat = DerivativeStrategyBase(symbol, side='short')
    snapshot = strat.make_snapshot('put', 0.15)
    snapshot_csv = SNAPSHOT_CSV_TEMPLATE.format(symbol=symbol, YYYYmmdd=config.NOW.strftime('%Y%m%d'))

    assert len(snapshot.df) > 0

    snapshot.df.reset_index(drop=True).to_csv(snapshot_csv, index=False, date_format=DATE_FORMAT)
