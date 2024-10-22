import pytest

import config

from datetime import datetime
from unittest.mock import patch

from strategy.builds import SellSimplePutBuild
from signals import MovingAverageSupportSignal, SignalAggregator


@patch('config.NOW', datetime(2024, 10, 21))
class TestSignalAggregator:
  
  @pytest.fixture
  def build(self):
    build = SellSimplePutBuild('TSLA', config.MY_WIN_PROBA)
    max_proba = 1 - config.MY_WIN_PROBA
    build.add_signal(MovingAverageSupportSignal(200, weight=0.5))
#    build.add_signal(FiftyTwoLowSupport())

    return signal_ag
  
  def test_calc_win_adv(self, build):
    result = build.calc_win_adv()

    assert result == 0.03  # 0.029645967

