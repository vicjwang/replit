import pytest
import pandas as pd

import config

from datetime import datetime
from io import StringIO
from unittest.mock import patch
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.extensions.amber import AmberSnapshotExtension

from constants import DATE_FORMAT
from strategy.base import DerivativeStrategyBase


class DataFrameSnapshotExtension(AmberSnapshotExtension):
  
  def matches(self, *, serialized_data, snapshot_data):
    print('vjw matches!')
    left_df = pd.read_csv(StringIO(serialized_data))
    right_df = pd.read_csv(StringIO(snapshot_data))
    pd.testing.assert_frame_equal(left_df, right_df)
    return True


class TestDerivativeStrategyBase:
  
  @pytest.fixture
  def snapshot_dataframe(self, snapshot):
    return snapshot.use_extension(DataFrameSnapshotExtension)

  @pytest.mark.skip()
  @patch('config.WORTHY_MIN_ROI', 0.2)
  def test_make_snapshot(self, snapshot):
    symbol = 'MDB'
    strat = DerivativeStrategyBase(symbol, side='short')
    result = strat.make_snapshot('put', 0.25).df.to_csv()
    
    print('vjw snapshot', dir(snapshot.session))
    snapshot_df = pd.DataFrame(snapshot.__dict__)
#    assert result == snapshot
    pd.testing.assert_frame_equal(result, snapshot_df)


  def test_test(self, snapshot_dataframe):
    df1 = pd.DataFrame({'a': [100,2,3], 'b': [4,5,6]})
    #pd.testing.assert_frame_equal(df1, snapshot_dataframe)
    assert snapshot_dataframe == df1
    
    
