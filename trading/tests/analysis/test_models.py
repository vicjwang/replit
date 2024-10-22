import pytest

from unittest.mock import patch
from datetime import datetime

from analysis.models import PriceModel


@patch('config.NOW', datetime(2024, 10, 16))
class TestModel:

  @pytest.fixture
  def model(self):
    model = PriceModel('TSLA')
    return model

  @patch('config.NOW', datetime(2024, 10, 16))
  def test_52_low(self, model):
    result = model.get_52_low()
    assert result == 218.16

  def test_52_high(self, model):
    result = model.get_52_high()
    assert result == 500.75

  def test_50_ma(self, model):
    result = model.get_ma(50)
    assert result == 271.14

  def test_200_ma(self, model):
    result = model.get_ma(200)
    assert result == 358.56

