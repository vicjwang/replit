import pandas as pd

from utils import fetch_past_earnings_dates, calc_expected_strike


def calc_historical_proba(symbol, prices, mu, sigma, trading_days):
  earnings_dates = fetch_past_earnings_dates(symbol)
  
  df = pd.DataFrame(prices)
  df['date'] = df['date']
  # Add column of expected price in n days.
  df['expected_price'] = df.apply(lambda x: calc_expected_strike(x['close'], mu, sigma, trading_days, 1), axis=1)

  # If start days is before earnings and n days later is after earnings, use None.
  df['expected_expiry'] = pd.to_datetime(df['date']) + pd.Timedelta(trading_days, unit='d')

  for earnings_date in earnings_dates:
    #print('vjw before earnings', (df['date'] < earnings_date).head())
    #print('vjw expiry after earnings', (df['expected_expiry'] > earnings_date).head())
    df.loc[(df['date'] < earnings_date) & (df['expected_expiry'] > earnings_date), 'expected_price'] = None
  
  # Add column of boolean if actual price < expeected price column (for cc).
  df['actual_price'] = df['close'].shift(trading_days)
  df['is_expectation_met'] = df['actual_price'] < df['expected_price']
  
  # Tally count of True values divide by total count.  
  proba = len(df[df['is_expectation_met'] == True])/len(df['expected_price'].dropna())

  return proba