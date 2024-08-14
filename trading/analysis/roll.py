import argparse
import pandas as pd

import config
from analysis.derivative_strategy import DerivativeStrategyBase
from constants import SIDE_SHORT, DATE_FORMAT, BOLD, BOLD_END

def find_roll_candidates(symbol, expiry, strike, premium, option_type='put'):
  
  ds = DerivativeStrategyBase(symbol, side=SIDE_SHORT)
  current_expiry_mask = ds.df['expiration_date'] == expiry 
  current_strike_mask = ds.df['strike'] == strike 
  current_type_mask = ds.df['option_type'] == option_type
  current_mask = current_expiry_mask & current_type_mask & current_strike_mask
  current = ds.df[current_mask].iloc[0]
  current_ask = current['ask']
  print(ds)
  print(f"Current holding: {current['description']}")
  print(f"Sold for ${premium}.")
  print(f"Current ask is ${current_ask}.")

  strike_mask = ds.df['strike'] <= strike if option_type == 'put' else ds.df['strike'] >= strike
  type_mask = ds.df['option_type'] == option_type
  dsdf_mask = strike_mask & type_mask
  dsdf = ds.df[dsdf_mask]
  for expiry_date in ds.expiry_dates[:4]:
    dte = (pd.Timestamp(expiry_date) - config.NOW).days
    print()
    print(expiry_date.strftime(DATE_FORMAT), f"({dte} days until expiry)")

    expiry_mask = dsdf['expiration_date'] == expiry_date
    mask = expiry_mask
    expiry_chain = dsdf[mask][::-1] if option_type == 'put' else dsdf[mask] # reverse to show in chronological order

    for index, row in expiry_chain.iterrows():
      desc = row['description']
      bid = row['bid']
      strike = row['strike']
      if bid <= .10:
        continue
      net = bid - current_ask
      agg = net + premium
      if agg < -1:
        continue
      print(f"{desc}: bid=${bid}, net=${net:.2f}, {BOLD if net > 0 else ''} agg=${agg:.2f} {BOLD_END if net > 0 else ''}")
    

if __name__ == '__main__':
  # Usage: poetry run python -m analysis.roll -t MDB -e 2024-08-09 -k 250 -c 2
  parser = argparse.ArgumentParser()
  parser.add_argument('-t', '--ticker')
  parser.add_argument('-e', '--expiry')
  parser.add_argument('-k', '--strike')
  parser.add_argument('-c', '--premium')
  parser.add_argument('-o', '--option_type')

  args = parser.parse_args()

  symbol = args.ticker
  expiry = args.expiry
  strike = float(args.strike) if args.strike else None
  premium = float(args.premium) if args.premium else None
  option_type = args.option_type if args.option_type else 'put'

  find_roll_candidates(symbol, expiry, strike, premium, option_type=option_type)
