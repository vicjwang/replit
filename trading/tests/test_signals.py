import pytest

import config

from datetime import datetime
from unittest.mock import patch

from strategy.builds import SellSimplePutBuild
from signals import MovingAverageSupportSignal


class TestSignals:
  
  @pytest.fixture
  def build(self):
    build = SellSimplePutBuild('DDOG', config.MY_WIN_PROBA)
    price_model = build.price_model
    max_proba = 1 - config.MY_WIN_PROBA
    build.add_signals([
      MovingAverageSupportSignal(200, price_model, weight=0.5)
    ])
#    build.add_signal(FiftyTwoLowSupport())

    return build
  
  def test_compute_edge(self, build, snapshot):
    result_df = build.create_snapshot().df
    result = result_df.iloc[0]['200_ma_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result == round(0.01364027538, 4)

