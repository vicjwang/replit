import pandas as pd

import config

from datetime import datetime

from constants import DATE_FORMAT
from analysis.derivative_strategy import DerivativeStrategyBase




class TestDerivativeStrategyBase:
  
  def test_build_snapshot(self):
    symbol = 'MDB'
    strat = DerivativeStrategyBase(symbol, side='short')
    snapshot = strat.build_snapshot('put', 0.15)

    result = snapshot.df
    expected = pd.read_csv(SNAPSHOT_CSV, parse_dates=['expiration_date'])
    print('vjw result\n', result[['description', 'bid', '0.15_target', 'yoy_roi']])
    print('vjw expected\n', expected[['description', 'bid', '0.15_target', 'yoy_roi']])

    pd.testing.assert_frame_equal(result, expected, check_dtype=False, check_like=True)


if __name__ == '__main__':
  # Usage: 
  # $ ENV=test poetry run python -m tests.test_derivative_strategy

#  symbol = 'MDB'
  symbols = 'AAPL,TSM,SNAP'.split(',')

  for symbol in symbols:
    strat = DerivativeStrategyBase(symbol, side='short')
    snapshot = strat.build_snapshot('put', 0.15)
    SNAPSHOT_CSV = 'tests/fixtures/{}-snapshot-{}.csv'.format(symbol, config.NOW.strftime('%Y%m%d'))

    assert len(snapshot.df) > 0

    snapshot.df.reset_index(drop=True).to_csv(SNAPSHOT_CSV, index=False, date_format=DATE_FORMAT)
