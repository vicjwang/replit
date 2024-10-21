import pytest

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

