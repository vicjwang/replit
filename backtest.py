import pandas as pd
import yfinance as yf
import os
import pickle

from utils import fetch_past_earnings_dates, calc_expected_strike


def calc_historical_itm_proba(symbol, prices, mu, sigma, trading_days, zscore, contract_type='c'):
  earnings_dates = fetch_past_earnings_dates(symbol)

  df = pd.DataFrame(prices)
  df['date'] = df['date']
  # Add column of expected price in n days.
  df['expected_price'] = df.apply(lambda x: calc_expected_strike(x['close'], mu, sigma, 1, zscore), axis=1)

  # If start days is before earnings and n days later is after earnings, use None.
  df['expected_expiry'] = pd.to_datetime(df['date']) + pd.Timedelta(trading_days, unit='d')

  for earnings_date in earnings_dates:
    df.loc[(df['date'] < earnings_date) & (df['expected_expiry'] > earnings_date), 'expected_price'] = None

  # Add column of boolean if actual price < expeected price column (for cc).
  df['actual_price'] = df['close'].shift(-1*trading_days)

  if contract_type == 'c':
    df['is_itm'] = df['actual_price'] >= df['expected_price']
  elif contract_type == 'p':
    df['is_itm'] = df['actual_price'] <= df['expected_price']

  # Tally count of True values divide by total count.
  proba = len(df[df['is_itm'] == True])/len(df['expected_price'].dropna())

  return proba



def cached():
    """
    A function that creates a decorator which will use "cachefile" for caching the results of the decorated function "fn".
    """
    def decorator(fn):  # define a decorator for a function "fn"
        def wrapped(*args, **kwargs):   # define a wrapper that will finally call "fn" with all arguments            
            # if cache exists -> load it and return its content
            if len(args) == 1:
              arglist = [args[0]]
            else:
              arglist = list(*args)
            cachefile = f'{fn.__name__}-{"_".join([arg for arg in arglist])}.pkl'
            if os.path.exists(cachefile):
                    with open(cachefile, 'rb') as cachehandle:
                        print("using cached result from '%s'" % cachefile)
                        return pickle.load(cachehandle)

            # execute the function with all arguments passed
            res = fn(*args, **kwargs)

            # write to cache file
            with open(cachefile, 'wb') as cachehandle:
                print("saving result to cache '%s'" % cachefile)
                pickle.dump(res, cachehandle)

            return res

        return wrapped

    return decorator


@cached()
def fetch_prices(symbol):
  df = yf.download(symbol, start='2010-01-01')
  return df


if __name__ == '__main__':
  prices = fetch_prices('AAPL')
  print(prices.head())
  
