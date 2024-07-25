import pandas as pd

import config

from datetime import datetime

from constants import DATE_FORMAT
from analysis.derivative_strategy import DerivativeStrategyBase


SNAPSHOT_CSV = 'tests/fixtures/MDB-snapshot-20240725.csv'


class TestDerivativeStrategyBase:
  
  def test_build_snapshot(self):
    symbol = 'MDB'
    strat = DerivativeStrategyBase(symbol, side='short')
    snapshot = strat.build_snapshot('put', 0.15)

    result = snapshot.df
    expected = pd.read_csv(SNAPSHOT_CSV, parse_dates=['expiration_date'])
    print('vjw res\n', result.head())
    print('vjw exp\n', expected.head())

    pd.testing.assert_frame_equal(result, expected, check_dtype=False, check_like=True)


if __name__ == '__main__':
  # Usage: 
  # $ ENV=test poetry run python -m tests.test_derivative_strategy

  symbol = 'MDB'
  strat = DerivativeStrategyBase(symbol, side='short')
  snapshot = strat.build_snapshot('put', 0.15)

  assert len(snapshot.df) > 0

  snapshot.df.reset_index(drop=True).to_csv(SNAPSHOT_CSV, index=False, date_format=DATE_FORMAT)


