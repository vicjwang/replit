import pandas as pd

from datetime import datetime, timedelta

from utils import fetch_past_earnings_dates, calc_expected_strike
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf


START_DATE = '2010-01-01'
SALE_START_DATE = '2025-04-01'


def execute_sale_plan(num_day, price, agg_df, plan_name='base_daily'):
  if plan_name == 'base_daily':
    # Sell equal amount every day
    if (datetime.today().date() + timedelta(days=num_day)) < datetime.strptime(SALE_START_DATE, '%Y-%m-%d').date():
      return
      
    agg_df['sale'] += price * 0.03
    agg_df['qty'] += 0.03
    


def run_mc_sim(symbol, num_days, ax=None):
  today = str(datetime.today().date())
  
  # Step 1: Download historical data
  prices = yf.download(symbol, start=START_DATE, end=today)
  print('before', len(prices))
  
  # Step 1a: Only use historical bull run dates.
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
  last_price = prices['Adj Close'][-1]

  # Step 4: Run the Monte Carlo Simulation
  simulation_df = pd.DataFrame()
  mu = bull_df['Returns'].mean()
  std = bull_df['Returns'].std()

  print(f'daily return: {mu}, sigma: {std}')

  my_df = pd.DataFrame()

  for x in range(num_simulations):
      price_series = [last_price]
      run_df = pd.DataFrame({
        'sale': [0],
        'qty': [0]
      })
      for num_day in range(num_days):
          price = price_series[-1] * np.exp(np.random.normal(mu, std))

          execute_sale_plan(num_day, price, run_df)
          price_series.append(price)
      simulation_df[x] = price_series

      my_df = pd.concat([my_df, run_df])

  print(f'Expected mean price in {num_days} days: ${round(np.mean(simulation_df.tail(1))):,}')
  print(f'Sale total mean: ${round(np.mean(my_df["sale"])):,}, stdev: ${round(np.std(my_df["sale"])):,}, sold qty: {np.mean(my_df["qty"]):,}')
  
  if ax:
    # Step 5: Plot the Simulation Results
    ax.plot(simulation_df)
    ax.title(f'Monte Carlo Simulation: {symbol} Price')
    ax.xlabel('Days')
    ax.ylabel('Price')
  else:
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
