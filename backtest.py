import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

from datetime import datetime, timedelta

from constants import SHOW_GRAPH
from utils import fetch_past_earnings_dates, calc_expected_strike


START_DATE = '2010-01-01'
SALE_START_DATE = '2025-04-01'
SALE_PLAN = 'weekly'
MAX_QTY = -1  # FILL IN
SALE_NUM_MONTHS = 6
SALE_NUM_WEEKS = SALE_NUM_MONTHS * 4
SALE_NUM_DAYS = SALE_NUM_MONTHS * 30


def parse_k_from_plan_name(plan_name):
  return int(plan_name.split('_')[1][:-2])
  

def execute_sale_plan(num_day, prices, agg_df, plan_name='weekly'):
  assert MAX_QTY > 0

  assert len(agg_df) == 1

  if agg_df['qty'][0] > MAX_QTY:
    return
  
  price = prices[-1]
  if (datetime.today().date() + timedelta(days=num_day)) < datetime.strptime(SALE_START_DATE, '%Y-%m-%d').date():
    return
  
  if 'daily' in plan_name:
    # Sell equal amount every day
    qty = MAX_QTY / SALE_NUM_DAYS
    
  elif 'weekly' in plan_name:  # seems to be optimal
    if num_day % 7 != 0:
      return
    qty = MAX_QTY / SALE_NUM_WEEKS

  elif 'monthly' in plan_name:
    if num_day % 30 != 0:
      return
    qty = MAX_QTY / SALE_NUM_MONTHS

  else:
    raise NotImplementedError

  # Parse moving average from plan_name.
  if 'ma' in plan_name:
    k = parse_k_from_plan_name(plan_name)
    ma = np.mean(prices[-1*k:])
    qty *= price / ma if price > ma else 0.00

  agg_df['sale'] += price * qty
  agg_df['qty'] += qty
  agg_df['max_price'] = [price] if price > agg_df['max_price'][0] else agg_df['max_price']

  return


def run_mc_sim(symbol, num_days, plan=SALE_PLAN, ax=None):
  today = str(datetime.today().date())
  
  # Step 0: Download historical data
  prices = yf.download(symbol, start=START_DATE, end=today)

  # Step 1a: Add useful columns.
  #k = parse_k_from_plan_name(plan_name)
  #prices['ma'] = prices['Adj Close'].rolling(window=k).mean()

  # Step 1b: Only use historical bull run dates.
  halvings = ('2012-11-28', '2016-07-09', '2020-05-11', '2024-04-19')
  halving_dates = [datetime.strptime(date, '%Y-%m-%d').date() for date in halvings]

  bull_df = pd.DataFrame()
  for halving_date in halving_dates:
    bull_df = pd.concat([bull_df, prices.loc[halving_date: halving_date + timedelta(days=30*18)]])

  # Step 2: Calculate daily returns
  bull_df['Returns'] = bull_df['Adj Close'].pct_change()
  

  # Step 3: Set up the simulation parameters
  num_simulations = 1000
  #num_days = 252  # Typically, there are 252 trading days in a year
  last_price = prices.iloc[-1]['Adj Close']

  # Step 4: Run the Monte Carlo Simulation
  
  mu = bull_df['Returns'].mean()
  std = bull_df['Returns'].std()

  print(f'daily return: {mu}, sigma: {std}')

  sim_dict = {}
  my_df = pd.DataFrame()

  for x in range(num_simulations):
      price_series = [last_price]
      run_df = pd.DataFrame({
        'sale': [0],
        'qty': [0],
        'max_price': [0],
      })
      for num_day in range(num_days):
          price = price_series[-1] * np.exp(np.random.normal(mu, std))
          price_series.append(price)

          execute_sale_plan(num_day, price_series, run_df, plan)
          
      sim_dict[x] = price_series

      my_df = pd.concat([my_df, run_df])

  simulation_df = pd.DataFrame(sim_dict)
  
  print(f'Expected mean price in {num_days} days: ${round(np.mean(simulation_df.tail(1))):,}')
  print(f'''Sale plan: \033[1m{plan}\033[0m
    expected total: ${round(np.mean(my_df["sale"])):,}
    expected stdev: ${round(np.std(my_df["sale"])):,}
    max total: ${round(np.max(my_df["sale"])):,}
    min total: ${round(np.min(my_df["sale"])):,}
    expected qty sold: {np.mean(my_df["qty"]):,}
    avg sale price: ${round(np.mean(my_df["sale"])/np.mean(my_df["qty"])):,}
    max price: ${round(np.max(my_df["max_price"])):,}
  ''')
  
  if ax:
    # Step 5: Plot the Simulation Results
    ax.plot(simulation_df)
    ax.title(f'Monte Carlo Simulation: {symbol} Price')
    ax.xlabel('Days')
    ax.ylabel('Price')
  elif SHOW_GRAPH:
    plt.figure(figsize=(10, 6))
    plt.plot(simulation_df)
    plt.title(f'Monte Carlo Simulation: {symbol} Stock Price')
    plt.xlabel('Days')
    plt.ylabel('Price')
    plt.show()
    


def calc_historical_itm_proba(symbol, prices, mu, sigma, trading_days, contract_type='c'):
  earnings_dates = fetch_past_earnings_dates(symbol)
  
  df = pd.DataFrame(prices)
  df['date'] = df['date']
  # Add column of expected price in n days.
  df['expected_price'] = df.apply(lambda x: calc_expected_strike(x['close'], mu, sigma, trading_days, 1), axis=1)

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
