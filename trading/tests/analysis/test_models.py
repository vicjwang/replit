import pytest
import config

from datetime import datetime

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

  @patch('analysis.models.fetch_latest_price', lambda _: 260.96)
  @patch('config.NOW', datetime(2024, 10, 26, 8, 00))  # NOTE: will not affect @cached()
  def test_latest_change_weekend(self, model):
    result = model.get_latest_change()
    assert round(result, 4) == -0.0003

  @patch('config.NOW', datetime(2024, 10, 24, 4, 00))  # NOTE: will not affect @cached()
  def test_latest_change_before_market_stale_data(self, model):
    result = model.get_latest_change()
    assert round(result, 4) == -0.0003

  @patch('config.NOW', datetime(2024, 10, 24, 11, 00))  # NOTE: will not affect @cached()
  def test_latest_change_market_hours_stale_data(self, model):
    result = model.get_latest_change()
    assert round(result, 4) == -0.0003

  @patch('analysis.models.fetch_latest_price', lambda _: 260.96)
  @patch('config.NOW', datetime(2024, 10, 23, 11, 00))  # NOTE: will not affect @cached()
  def test_latest_change_market_hours_fresh_data(self, model):
    result = model.get_latest_change()
    assert round(result, 4) == -0.0125

  @patch('analysis.models.fetch_latest_price', lambda _: 260.96)
  @patch('config.NOW', datetime(2024, 10, 24, 17, 00))  # NOTE: will not affect @cached()
  def test_latest_change_after_hours_stale_data(self, model):
    result = model.get_latest_change()
    assert round(result, 4) == -0.0003

  @patch('analysis.models.fetch_latest_price', lambda _: 260.96)
  @patch('config.NOW', datetime(2024, 10, 23, 17, 00))  # NOTE: will not affect @cached()
  def test_latest_change_after_hours_fresh_data(self, model):
    result = model.get_latest_change()
    assert round(result, 4) == -0.0125

  def test_start_date(self, model):
    result = model.start_date
    assert result == '2023-10-10'

  def test_start_date_default(self):
    model = PriceModel('FSLY')  # would never invest.
    result = model.start_date
    assert result == '2023-01-01'
