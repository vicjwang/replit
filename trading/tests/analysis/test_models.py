import pytest

from unittest.mock import patch

from analysis.models import PriceModel


class TestModel:

  @pytest.fixture
  def model(self):
    model = PriceModel('MDB')
    return model

  def test_52_low(self, model):
    result = model.get_52_low()
    assert result == 218.16

  def test_52_high(self, model):
    result = model.get_52_high()
    assert result == 500.75

  def test_50_ma(self, model):
    result = model.get_ma(50)
    assert result == 270.99

  def test_200_ma(self, model):
    result = model.get_ma(200)
    assert result == 320.99

  @patch('analysis.models.is_market_hours', lambda: True)
  def test_latest_change_during_market_hours(self, model):
    result = model.get_latest_change()
    # Snapshot was taken outside market hours so expect tiny difference.
    assert round(result) == 0

  def test_latest_change_outside_market_hours(self, model):
    result = model.get_latest_change()
    assert round(result, 4) == -0.0131
