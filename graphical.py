
import json
import pandas as pd

from utils import calc_annual_roi

from constants import DELTA_UPPER


def render_roi_vs_expiry(symbol, chains, atm_strike, ax=None, params=None):
  if not ax:
    raise ValueError('No ax to graph on.')

  # Store all chains in DataFrame.
  df = pd.DataFrame()
  for chain in chains:
    df = pd.concat([df, pd.DataFrame.from_records(chain)], axis=0)

  # Unnest greek columns.
  df = pd.concat([df, df['greeks'].apply(pd.Series)], axis=1)
  
  df['annual_roi'] = df.apply(calc_annual_roi, axis=1)

  # Capture closest strikes.
  buffer = max(round(atm_strike / 90), 0.50)
  buffer_mask = (abs(df['strike'] - df['target_strike']) < buffer)

  # ROI needs to be worth it plus ROI becomes linear when too itm so remove.
  roi_mask = (df['annual_roi'] > 0.2) & (df['annual_roi'] < 1)

  # Cash needs to be worth it per contract.
  cash_mask = (df['bid'] > 0.7) 

  mask = buffer_mask & roi_mask & cash_mask
  
  rois = df[mask]['annual_roi']
  expirations = df[mask]['expiration_date']
  strikes = df[mask]['strike']
  bids = df[mask]['bid']
  deltas = df[mask]['delta']

  if len(expirations) == 0:
    raise ValueError(f'No suitable options found for {symbol}.')

  # Graph of ROI vs Expirations.
  ax.plot(expirations, rois)
  for x, y, strike, bid, delta in zip(expirations, rois, strikes, bids, deltas):
    label = f'K=\${strike}; \${bid} ({DELTA_UPPER}={round(delta, 2)})'
    ax.text(x, y, label, fontsize=8)#, ha='right', va='bottom')

  if params:
    if 'title' in params:
      title = params['title']
      ax.set_title(title)
    if 'text' in params:
      text = params['text']
      bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
      ax.text(0.75, 0.95, text, transform=ax.transAxes, fontsize=10,
              verticalalignment='top', bbox=bbox_props)
    if 'ylabel' in params:
      ylabel = params['ylabel']
      ax.set_ylabel(ylabel)

