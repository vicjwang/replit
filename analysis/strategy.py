import pandas as pd

from analysis.models import PriceModel

from constants import (
  DELTA_UPPER,
  PHI_ZSCORE,
  MU,
  SIGMA_LOWER,
  MY_WIN_PROBA,
  WIN_PROBA_ZSCORE,
  WORTHY_MIN_ROI,
  WORTHY_MIN_BID,
)

from vendors.tradier import (
  fetch_options_expirations,
  fetch_options_chain,
)

from utils import (
  calc_dte,
  calc_annual_roi,
)


class DerivativeStrategy:
  # TODO (vjw): remove option_type?
  def __init__(self, symbol, option_type='call', side='short'):
    self.symbol = symbol
    self.option_type = option_type
    self.price_model = PriceModel(symbol)
    self.side = side
  
    self.expiry_dates = pd.to_datetime(fetch_options_expirations(symbol))
    self._load()

  # TODO (vjw): use_cache from pkl?
  def _load(self, use_cache=True):
  
    self.df = pd.DataFrame()
    
    # Target strikes depend on expiry dates so concat by expiry date groups.
    for expiry_date in self.expiry_dates:

      chain = fetch_options_chain(self.symbol, expiry_date.strftime('%Y-%m-%d'))
      if not chain:
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

  # TODO (vjw): use @property?
  def get_price_model(self):
    return self.price_model

  def prepare_graph_data(self, zscore, start_date=None, end_date=None):
    
    # Capture closest strikes.
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

  def pprint(self):
    self.price_model.pprint()
#    for e, t in sorted(set(zip(self.expiry_dates, target_strikes))):
#      self._print(f'{e} target=${t:.2f}')

  def _print(self, s):
    text = f"{self.symbol}: {s}"
    print(text)
    return text

  def graph_roi_vs_expiry(self, ax, target_colname=None):

    if target_colname is None:
      zscore = WIN_PROBA_ZSCORE[self.side][self.option_type][MY_WIN_PROBA]
      target_colname = f"{zscore}_sigma_target"

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

    # Graph of ROI vs Expirations.
    self._print(f'Adding subplot (WORTHY_MIN_BID={WORTHY_MIN_BID}, WORTHY_MIN_ROI={WORTHY_MIN_ROI})')
    ax.plot(expirations, rois)
    for x, y, strike, bid, delta in zip(expirations, rois, strikes, bids, deltas):
      label = f'K=\${strike}; \${bid} ({DELTA_UPPER}={round(delta, 2)})'
      ax.text(x, y, label, fontsize=8)#, ha='right', va='bottom')

    # Custom xticks.
    xticks = expirations
    xticklabels = [f'{e}\n(t=${t})' for e,t in zip(expirations, target_strikes)]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=30)

    title = self._print(f"{self.side.title()} {self.option_type.title()} ({MY_WIN_PROBA}% Win Proba)")
    ax.set_title(title)

    text = '\n'.join((
      f'\${latest_price}, {round(latest_change * 100, 2)}%',
      f'Next earnings: {self.price_model.get_next_earnings_date().date()}',
      f'{MU}={mu * 100:.2f}%',
      f'{SIGMA_LOWER}={sigma * 100:.2f}%',
    ))
    bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.75, 0.95, text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=bbox_props)

    ylabel= 'ROI (YoY)'
    ax.set_ylabel(ylabel)
