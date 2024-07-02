import math
import pandas as pd
import numpy as np
import sys

from vendors.tradier import (
  fetch_historical_prices,
  fetch_past_earnings_dates,
  fetch_options_expirations,
  fetch_options_chain,
)

from utils import (
  calc_dte,
  calc_annual_roi,
)

from constants import (
  DELTA_UPPER,
  START_DATE,
  SHOULD_AVOID_EARNINGS,
  PHI_ZSCORE,
  MU,
  SIGMA_LOWER,
  MY_PHI,
  WORTHY_MIN_ROI,
  WORTHY_MIN_BID,
  ZSCORE_PHI,
)


class PriceModel:
  
  _COLNAME_DAILY_CHANGE = 'daily_change'
  _COLNAME_IS_EARNINGS = 'is_earnings'
  _COLNAME_CLOSE = 'close'
  _COLNAME_DATE = 'date'
  _COLNAME_PREV_DAY = 'previous_trading_date'

  def __init__(self, symbol, start_date=START_DATE):
    self.symbol = symbol

    # Sorted in most recent first.
    self.earnings_dates = fetch_past_earnings_dates(symbol)

    # Some helper columns.
    self.prices_df = pd.DataFrame(fetch_historical_prices(symbol, start_date))
    self.prices_df[self._COLNAME_DATE] = pd.to_datetime(self.prices_df[self._COLNAME_DATE])
    self.prices_df[self._COLNAME_DAILY_CHANGE] = self.prices_df[self._COLNAME_CLOSE].pct_change(periods=1)
    self.prices_df[self._COLNAME_PREV_DAY] = pd.to_datetime(self.prices_df[self._COLNAME_DATE].shift(1))
    self.prices_df[self._COLNAME_IS_EARNINGS] = self.prices_df[self._COLNAME_DATE].isin(self.earnings_dates) | self.prices_df[self._COLNAME_PREV_DAY].isin(self.earnings_dates)
 
    # Use mask to include/exclude price movements on earnings dates.
    mask = [True] * len(self.prices_df)
    if SHOULD_AVOID_EARNINGS:
      mask = ~self.prices_df[self._COLNAME_IS_EARNINGS]

    # Save some key stats.
    self.daily_mean = self.prices_df[mask][self._COLNAME_DAILY_CHANGE].mean()
    self.daily_stdev = self.prices_df[mask][self._COLNAME_DAILY_CHANGE].std()
    self.print(f"{MU}={self.daily_mean} {SIGMA_LOWER}={self.daily_stdev}")

  def print(self, s):
    print(f"{self.symbol}: {s}")
  
  def get_latest_price(self):
    return self.prices_df.iloc[-1][self._COLNAME_CLOSE]

  def get_latest_change(self):
    return self.prices_df.iloc[-1][self._COLNAME_DAILY_CHANGE]

  def get_daily_mean(self):
    return self.daily_mean

  def get_daily_stdev(self):
    return self.daily_stdev

  def predict_price(self, days, zscore):
    latest_price = self.get_latest_price()
    mu = self.get_daily_mean()
    sigma = self.get_daily_stdev()
    target_price = latest_price * (1 + days*mu + zscore*math.sqrt(days)*sigma)
    return target_price

  def print_latest(self):
    latest_price = self.get_latest_price() 
    latest_change = self.get_latest_change()
    print(f'{self.symbol}: ${latest_price}, {round(latest_change * 100, 2)}%')
   

class DerivativeDataFrame:
  # TODO (vjw): remove option_type?
  def __init__(self, symbol, option_type='call', price_model=None):
    self.symbol = symbol
    self.option_type = option_type
    self.price_model = price_model
  
    self.expiry_dates = pd.to_datetime(fetch_options_expirations(symbol))
    self._load_dataframe()


  # TODO (vjw): use_cache from pkl?
  def _load_dataframe(self, use_cache=True):
  
    self.df = pd.DataFrame()
    
    for expiry_date in self.expiry_dates:

      chain = fetch_options_chain(self.symbol, expiry_date.strftime('%Y-%m-%d'))
      if not chain:
        continue

      if not self.price_model:
        continue

      chain_df = pd.DataFrame.from_records(chain)
      chain_df = chain_df[chain_df['option_type'] == self.option_type]

      dte = calc_dte(expiry_date.strftime('%Y-%m-%d'))
      for _zscore in sorted(PHI_ZSCORE.values()):
        zscore = _zscore if self.option_type == 'call' else -1*_zscore
        target_strike = self.price_model.predict_price(dte, zscore)

        colname = f"{zscore}_sigma_target"
        chain_df[colname] = target_strike

      self.df = pd.concat([self.df, chain_df], axis=0)

    # Helper columns including unnested greek columns.
    self.df = pd.concat([self.df, self.df['greeks'].apply(pd.Series)], axis=1)
    del self.df['greeks']
    self.df['yoy_roi'] = self.df.apply(calc_annual_roi, axis=1)
    self.df['expiration_date'] = pd.to_datetime(self.df['expiration_date'])

  def prepare_graph_data(self, start_date=None, end_date=None):
    
    # Capture closest strikes.
    zscore = PHI_ZSCORE[MY_PHI] if self.option_type == 'call' else -1*PHI_ZSCORE[MY_PHI]
    buffer = 3 # max(round(atm_strike * 0.05), 0.50)
    buffer_mask = (abs(self.df['strike'] - self.df[f"{zscore}_sigma_target"]) < buffer)

    # ROI needs to be worth it plus ROI becomes linear when too itm so remove.
    roi_mask = (self.df['yoy_roi'] > WORTHY_MIN_ROI)
    otm_only_mask = (self.df['yoy_roi'] < 1)

    # Cash needs to be worth it per contract.
    cash_mask = (self.df['bid'] > WORTHY_MIN_BID) 

    mask = cash_mask & buffer_mask & roi_mask & otm_only_mask

    if start_date:
      start_mask = (self.df['expiration_date'] > start_date)
      mask &= start_mask

    if end_date:
      end_mask = (self.df['expiration_date'] < end_date)
      mask &= end_mask

    self.graph_df = self.df[mask]

    if len(self.graph_df) == 0:
      raise ValueError(f'No eligible options for graph found.')

  def print(self, s):
    text = f"{self.symbol}: {s}"
    print(text)
    return text

  def graph_roi_vs_expiry(self, ax, target_colname):

    zscore = PHI_ZSCORE[MY_PHI] if self.option_type == 'call' else -1*PHI_ZSCORE[MY_PHI]

    mu = self.price_model.get_daily_mean()
    sigma = self.price_model.get_daily_stdev()
    latest_price = self.price_model.get_latest_price()
    latest_change = self.price_model.get_latest_change()

    rois = self.graph_df['yoy_roi']
    expirations = self.graph_df['expiration_date']
    strikes = self.graph_df['strike']
    bids = self.graph_df['bid']
    deltas = self.graph_df['delta']
    target_strikes = self.graph_df[target_colname].round(2)

    for e, t in sorted(set(zip(expirations, target_strikes))):
      self.print(f'{e} target=${t:.2f}')

    # Graph of ROI vs Expirations.
    self.print(f'Adding subplot (WORTHY_MIN_BID={WORTHY_MIN_BID}, WORTHY_MIN_ROI={WORTHY_MIN_ROI})')
    ax.plot(expirations, rois)
    for x, y, strike, bid, delta in zip(expirations, rois, strikes, bids, deltas):
      label = f'K=\${strike}; \${bid} ({DELTA_UPPER}={round(delta, 2)})'
      ax.text(x, y, label, fontsize=8)#, ha='right', va='bottom')

    # Custom xticks.
    xticks = expirations
    xticklabels = [f'{e}\n(t=${t})' for e,t in zip(expirations, target_strikes)]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=30)

    title = self.print(f"{self.option_type.title()} strikes @ Z-Score={zscore} ({ZSCORE_PHI[self.option_type][zscore]}% ITM confidence)")
    ax.set_title(title)

    text = '\n'.join((
     f'\${latest_price}, {round(latest_change * 100, 2)}%',
#vjw     f'Next earnings: {next_earnings_date.date()}',
     f'{MU}={mu * 100:.2f}%',
     f'{SIGMA_LOWER}={sigma * 100:.2f}%',
    )),
    bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.75, 0.95, text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=bbox_props)

    ylabel= 'ROI (YoY)',
    ax.set_ylabel(ylabel)
