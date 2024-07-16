import yfinance as yf


def fetch_earnings_dates(symbol):
  stock = yf.Ticker(symbol)
  earnings_dates = [x.date() for x in stock.get_earnings_dates(limit=28).index]
  return earnings_dates
