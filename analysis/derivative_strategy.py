import mplcursors
import matplotlib.dates as mdates
import pandas as pd

from analysis.models import PriceModel
from constants import (
  DATE_FORMAT,
  DELTA_UPPER,
  PHI_ZSCORE,
  MU,
  SIGMA_LOWER,
  MAX_STRIKE,
  MY_WIN_PROBA,
  WIN_PROBA_ZSCORE,
  WORTHY_MIN_BID,
  WORTHY_MIN_ROI,
)
from utils import (
  count_trading_days,
  calc_annual_roi,
  get_win_proba,
  get_target_colname,
)
from vendors.tradier import (
  fetch_options_expirations,
  fetch_options_chain,
)


class DerivativeStrategyBase:
  INCLUDE_COLUMNS = [
    'expiration_date',
    'option_type',
    'strike',
    'bid',
    'volume',
    'greeks',
  ]
  
  def __init__(self, symbol, side=None):
    self.symbol = symbol
    self.price_model = PriceModel(symbol)
    self.side = side
  
    self.expiry_dates = pd.to_datetime(fetch_options_expirations(symbol))
    self._load()

  def __repr__(self):
    return f"DerivativeStrategyBase(symbol={self.symbol}, side={self.side})"

  def __str__(self):
    return str(self.price_model)

  # TODO (vjw): use_cache from pkl?
  def _load(self, use_cache=True):
  
    self.df = None
    
    zscores = sorted(PHI_ZSCORE.values())

    chain_dfs = []
    # Target strikes depend on expiry dates so concat by expiry date groups.
    for expiry_date in self.expiry_dates:

      chain = fetch_options_chain(self.symbol, expiry_date.strftime(DATE_FORMAT))
      # Drop column if all values = nan.
      chain_df = pd.DataFrame.from_records(chain, columns=self.INCLUDE_COLUMNS).dropna(axis=1, how='all')
#      chain_df = pd.DataFrame.from_records(chain).dropna(axis=1, how='all')

      if chain_df.empty:
        continue

      trading_dte = count_trading_days(expiry_date)
      for zscore in zscores:
        target_strike = self.price_model.predict_price(trading_dte, zscore)
        colname = f"{zscore}_sigma_target"
        chain_df[colname] = target_strike

      chain_dfs.append(chain_df)
      
    # Optimization - concat just once at end, otherwise copy created per loop.
    self.df = pd.concat(chain_dfs, axis=0)

    # Helper columns including unnested greek columns.
    greeks = pd.json_normalize(self.df['greeks']).set_index(self.df.index)
    self.df = pd.concat([self.df.drop(columns=['greeks']), greeks], axis=1)

    self.df['yoy_roi'] = self.df.apply(calc_annual_roi, axis=1)

  # TODO (vjw): use @property?
  def get_price_model(self):
    return self.price_model

  def build_snapshot(self, option_type, zscore=None, expiry_after=None, expiry_before=None):

    if option_type not in ('call', 'put'):
      raise ValueError("Invalid option_type: {option_type}")

    if zscore is None:
      zscore = WIN_PROBA_ZSCORE[self.side][option_type][MY_WIN_PROBA]
      win_proba = MY_WIN_PROBA
    else:
      win_proba = get_win_proba(self.side, option_type, zscore)

    # Capture closest 2 strikes.
    target_colname = get_target_colname(zscore)
    graph_df = self.df.groupby(by='expiration_date').apply(lambda x: x.iloc[(abs(x['strike'] - x[target_colname])).argsort()[:2]])

    strike_mask = (graph_df['strike'] < MAX_STRIKE)

    option_type_mask = (graph_df['option_type'] == option_type)

    # ROI needs to be worth it plus ROI becomes linear when too itm so remove.
    roi_mask = (graph_df['yoy_roi'] > WORTHY_MIN_ROI)
    otm_only_mask = (graph_df['yoy_roi'] < 1)

    # Cash needs to be worth it per contract.
    cash_mask = (graph_df['bid'] > WORTHY_MIN_BID) 

    mask = option_type_mask & strike_mask & cash_mask & roi_mask & otm_only_mask

    if expiry_after:
      start_mask = (graph_df['expiration_date'] > expiry_after)
      mask &= start_mask

    if expiry_before:
      end_mask = (graph_df['expiration_date'] < expiry_before)
      mask &= end_mask

    graph_df = graph_df[mask].reset_index(drop=True)

    if len(graph_df) == 0:
      raise ValueError(f"No eligible options to graph (option_type={option_type}, expiry_after={expiry_after}, expiry_before={expiry_before}).")

    mu = self.price_model.get_daily_mean()
    sigma = self.price_model.get_daily_stdev()
    latest_price = self.price_model.get_latest_price()
    latest_change = self.price_model.get_latest_change()
    next_earnings = self.price_model.get_next_earnings_date()

    title = f"{self.symbol}: {self.side.title()} {option_type.title()} Strikes @ Z-Score={zscore} ({win_proba}% Win Proba)"
    text = '\n'.join((
      f'${latest_price}, {latest_change * 100:.2f}%',
      f'Next earnings: {next_earnings.strftime(DATE_FORMAT)}',
      f'{MU}={mu * 100:.2f}%',
      f'{SIGMA_LOWER}={sigma * 100:.2f}%',
    ))
    return DerivativeStrategySnapshot(self.symbol, graph_df, self.side, option_type,
                                      zscore, title=title, text=text, next_earnings=next_earnings)


class DerivativeStrategySnapshot:
  
  def __init__(self, symbol, df, side, option_type, zscore, title=None, text=None, next_earnings=None):
    self.symbol = symbol
    self.df = df
    self.title = title
    self.text = text
    self.side = side
    self.option_type = option_type
    self.zscore = zscore
    self.next_earnings = next_earnings

  def graph_roi_vs_expiry(self, ax):
    target_colname = get_target_colname(self.zscore)

    rois = self.df['yoy_roi']
    expirations = self.df['expiration_date']
    strikes = self.df['strike']
    bids = self.df['bid']
    deltas = self.df['delta']
    target_strikes = self.df[target_colname].round(2)

    if len(expirations) == 0:
      raise RuntimeError('No data to graph')

    # Graph of ROI vs Expirations.
    xs = pd.to_datetime(expirations)
    ys = rois
    ax.plot(xs, ys, linestyle='-', marker='o')
    scatter = ax.scatter(xs, ys)
    for x, y, strike, bid, delta in zip(xs, ys, strikes, bids, deltas):
      label = f'K=${strike}; ${bid} ({DELTA_UPPER}={delta:.2f})'
      ax.text(x, y, label, fontsize=8)#, ha='right', va='bottom')

    # Custom xticks.
    xticks = xs
    xticklabels = [f'{e.strftime(DATE_FORMAT)}\n(t=${t})' for e,t in zip(xs, target_strikes)]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=30)

    cursor = mplcursors.cursor(scatter, hover=True)

    vols = self.df['smv_vol']
    volumes = self.df['volume']
    thetas = self.df['theta']
    gammas = self.df['gamma']
    vegas = self.df['vega']
    tooltip_map = dict()
    for i, expiry in enumerate(xs):
      expiry_at = expiry.strftime(DATE_FORMAT)
      target_strike = target_strikes.iloc[i]
      strike = strikes.iloc[i]
      bid = bids.iloc[i]
      volume = volumes.iloc[i]
      vol = vols.iloc[i].round(4)
      delta = deltas.iloc[i].round(4)
      theta = thetas.iloc[i].round(4)
      gamma = gammas.iloc[i].round(4)
      vega = vegas.iloc[i].round(4)
      tooltip_map[expiry_at] = (target_strike, strike, bid, volume, vol, delta, theta, gamma, vega)

    @cursor.connect('add')
    def on_add(sel):
      expiry_at = mdates.num2date(sel.target[0]).strftime(DATE_FORMAT)
      roi = sel.target[1]
      target_strike, strike, bid, volume, vol, delta, theta, gamma, vega = tooltip_map[expiry_at]
      text = '\n'.join([
        f"expiry={expiry_at}",
        f"target=${target_strike}",
        f"strike=${strike}",
        f"bid=${bid}",
        f"volume={volume}",
        f"vol={vol}",
        f"delta={delta}",
        f"theta={theta}",
        f"gamma={gamma}",
        f"vega={vega}"
      ])

      sel.annotation.set(text=text)
    
    yticks = [i/10 for i in range(2, 10)]
    ax.set_yticks(yticks)

    win_proba = get_win_proba(self.side, self.option_type, self.zscore)
    ax.set_title(self.title)

    bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.75, 0.95, self.text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=bbox_props)

    ylabel= 'ROI (YoY)'
    ax.set_ylabel(ylabel)

    ax.axvline(x=self.next_earnings, color='b')

