import argparse
import pandas as pd

from analysis.models import PriceModel
from constants import T_SIG_LEVELS 
from utils import get_tscore
from vendors.tradier import fetch_historical_prices


def find_best_regime_start_date(symbol, start_dates):
  
  for start_date in start_dates:
    
    model = PriceModel(symbol, start_date=start_date)
    regime_df = pd.DataFrame(columns=['start_date', 'dte', 'siglevel', 'itm_proba', 'diff'])
  
    for dte in range(5, 21):
      df = pd.DataFrame()

      for sig_level in T_SIG_LEVELS[3:12]:

        target_colname = '[{}]{}_dte_{}_target'.format(start_date, dte, sig_level)

        tscore = get_tscore(sig_level, dte)
        df[target_colname] = model.prices_df.apply(lambda row: model.predict_price(dte, tscore, row['close']), axis=1)

        actual_colname = '[{}]{}_dte_{}_actual'.format(start_date, dte, sig_level)
        df[actual_colname] = model.prices_df['close'].shift(-1 * dte)

        itm_colname = '[{}]{}_dte_{}_is_itm_put'.format(start_date, dte, sig_level)

        df[itm_colname] = df[actual_colname] <= df[target_colname]
  
        proba = len(df[df[itm_colname] == True]) / len(df.index)
        diff = proba - sig_level

        regime_df.loc[len(regime_df.index)] = [start_date, dte, sig_level, proba, diff]

    print('[{}]'.format(symbol), start_date, 'error squared:', ((regime_df['itm_proba'] - regime_df['siglevel'])**2).sum())
    print()


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-t', '--tickers', required=True)

  args = parser.parse_args()
  tickers = args.tickers.upper().split(',')

  start_dates = [
    '2022-01-01',  # includes bear market
    '2023-01-01',  # FED signals rate cut
    '2024-01-01',
  ]

  for ticker in tickers:
    find_best_regime_start_date(ticker, start_dates)


