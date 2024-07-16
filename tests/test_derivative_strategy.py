import pandas as pd

from analysis.derivative_strategy import DerivativeStrategyBase


SNAPSHOT_CSV = 'tests/fixtures/MDB-20240715-snapshot.csv'


class TestDerivativeStrategyBase:
  
  def test_build_snapshot(self):
    symbol = 'MDB'
    strat = DerivativeStrategyBase(symbol, side='short')
    snapshot = strat.build_snapshot('put', -1)

    result = snapshot.df
    expected = pd.read_csv(SNAPSHOT_CSV)

    pd.testing.assert_frame_equal(result, expected, check_dtype=False, check_like=True)


if __name__ == '__main__':
  symbol = 'MDB'
  strat = DerivativeStrategyBase(symbol, side='short')
  snapshot = strat.build_snapshot('put', -1)

  assert len(snapshot.df) > 0

  snapshot.df.reset_index(drop=True).to_csv(SNAPSHOT_CSV, index=False)
