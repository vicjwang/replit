import pandas as pd
from datetime import date

from vendors.tradier import get_next_earnings_date


def test_get_next_earnings_date():
  symbol = 'TSLA'
  result = get_next_earnings_date(symbol)
  actual = pd.to_datetime('2024-07-23')
  assert result == actual
