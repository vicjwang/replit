import pandas as pd

import config

from datetime import datetime
from freezegun import freeze_time

from constants import DATE_FORMAT
from analysis.derivative_strategy import DerivativeStrategyBase


SNAPSHOT_CSV = 'tests/fixtures/MDB-snapshot-20240716.csv'


class TestDerivativeStrategyBase:
  
  @freeze_time(config.FROZEN_TEST_DATE)
  def test_build_snapshot(self):
    symbol = 'MDB'
    strat = DerivativeStrategyBase(symbol, side='short')
    snapshot = strat.build_snapshot('put', -1)

    result = snapshot.df
    expected = pd.read_csv(SNAPSHOT_CSV, parse_dates=['expiration_date'])

    pd.testing.assert_frame_equal(result, expected, check_dtype=False, check_like=True)


if __name__ == '__main__':
  symbol = 'MDB'
  strat = DerivativeStrategyBase(symbol, side='short')
  snapshot = strat.build_snapshot('put', -1)

  assert len(snapshot.df) > 0

  snapshot.df.reset_index(drop=True).to_csv(SNAPSHOT_CSV, index=False, date_format=DATE_FORMAT)
