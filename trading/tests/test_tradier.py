import pandas as pd

import config

from datetime import date
from unittest.mock import patch

from vendors.tradier import fetch_next_earnings_date
from constants import DATE_FORMAT


def test_get_next_earnings_date_is_today():
  symbol = 'TSLA'
  today = pd.Timestamp(config.NOW.date())
  mock_earnings_dates = pd.to_datetime([
    '2024-10-18',
    today,
  ])
  with patch('vendors.tradier.fetch_earnings_dates', return_value=mock_earnings_dates):
    result = fetch_next_earnings_date(symbol)
    actual = pd.Timestamp(today)
    assert result == actual
