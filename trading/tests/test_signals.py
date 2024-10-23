import pytest

import config

from datetime import datetime
from unittest.mock import patch

from strategy.builds import SellSimplePutBuild
from signals import MovingAverageSupportSignal


@patch('config.NOW', datetime(2024, 10, 22))
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
  
  def test_compute_edge(self, build):
    print('vjw config', config.NOW)
    snapshot = build.create_snapshot()
    result = snapshot.df.iloc[0]['200_ma_edge'].round(4)

    assert len(snapshot.df) == 1  # Next earnings is Nov 7 so only 1 week of options.
    assert result == round(0.01364027538, 4)

