import config

from datetime import datetime

from unittest.mock import patch

from utils import is_market_hours


class TestUtils:
  # TODO: vjw add hypothesis testing?

  @patch('config.NOW', datetime(2024, 10, 24, 11, 0))
  def test_is_market_hours_true(self):
    result = is_market_hours()
    assert result

  def test_is_market_hours_premarket(self):
    result = is_market_hours()
    assert result is False

  @patch('config.NOW', datetime(2024, 10, 24, 20, 0))
  def test_is_market_hours_afterhours(self):
    result = is_market_hours()
    assert result is False
