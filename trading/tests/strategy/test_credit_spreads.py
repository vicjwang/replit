import pandas as pd
from unittest.mock import patch

import config

from datetime import datetime

from constants import DATE_FORMAT
from strategy.credit_spreads import CreditSpreadStrategy


SNAPSHOT_CSV_TEMPLATE = 'tests/fixtures/MDB-credit-spreads-snapshot-{YYYYmmdd}.csv'


class TestCreditSpreadStrategy:
  
  @patch('config.NOW', datetime(2024, 10, 16))
  def test_make_snapshot(self):
    symbol = 'MDB'
    strat = CreditSpreadStrategy(symbol, side='short')
    snapshot = strat.make_snapshot('put', 0.15)

    result = snapshot.df
    snapshot_csv = SNAPSHOT_CSV_TEMPLATE.format(YYYYmmdd=config.NOW.strftime('%Y%m%d'))
    expected = pd.read_csv(snapshot_csv, parse_dates=['expiration_date'])

    pd.testing.assert_frame_equal(result, expected, check_dtype=False, check_like=True)


if __name__ == '__main__':
  # Usage: 
  # $ ENV=test poetry run python -m tests.test_derivative_strategy

  symbol = 'MDB'
  strat = CreditSpreadStrategy(symbol, side='short')
  snapshot = strat.make_snapshot('put', 0.15)
  snapshot_csv = SNAPSHOT_CSV_TEMPLATE.format(YYYYmmdd=config.NOW.strftime('%Y%m%d'))

  assert len(snapshot.df) > 0

  snapshot.df.reset_index(drop=True).to_csv(snapshot_csv, index=False, date_format=DATE_FORMAT)
