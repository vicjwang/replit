import pytest


class TestSignalAggregator:
  
  @pytest.fixture
  def signal_agg(self):
    model = PriceModel('MDB')
    max_proba = 0.25
    signal_agg = SignalAggregator(model, max_proba)
    signal_agg.add_signal(MovingAverageSupport(200))
    signal_agg.add_signal(FiftyTwoLowSupport())

    return signal_agg
  
  def test_calc_ev_advantage(self, signal_agg):
    result = signal_agg.calc_ev_advantage()

    assert result == False
    

