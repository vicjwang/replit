from collections import namedtuple


SHOW_GRAPHS = False
IS_DEBUG = False
IS_VERBOSE = False
START_DATE = '2023-01-01'
SHOULD_AVOID_EARNINGS = True
USE_EARNINGS_CSV = False

WORTHY_MIN_BID = 0.7
WORTHY_MIN_ROI = 0.2

REFERENCE_CONFIDENCE = {
  0: 0.5,
  1: 0.158,
  -1: 0.158,
  -3: .99,
}
NOTABLE_DELTA_MAX = .2

FIG_WIDTH = 13.5
FIG_HEIGHT = 7.5


# Using Unicode escape sequences
DELTA_UPPER = '\u0394'
DELTA_LOWER = '\u03B4'
SIGMA_UPPER = '\u03A3'
SIGMA_LOWER = '\u03C3'
MU = '\u03BC'


Ticker = namedtuple('Ticker', ['symbol', 'name', 'next_earnings'], defaults=(None, None, None))

TICKERS = [
  Ticker('AAPL', name='Apple Inc.', next_earnings='2024-07-26'),
  Ticker(symbol='ABNB', name='Airbnb', next_earnings='2024-08-01'),
  Ticker(symbol='AMZN', name='amazon', next_earnings='2024-08-01'),
  Ticker(symbol='BRK/B', name='berkshire'),
  Ticker('CRM', name='Salesforce'),
  Ticker(symbol='CRWD', name='crowdstrike', next_earnings='2024-06-04'),
  Ticker(symbol='DIS', name='disney', next_earnings='2024-08-14'),
  Ticker(symbol='DDOG', name='datadog', next_earnings='2024-08-07'),
  Ticker(symbol='GOOG', name='google', next_earnings='2024-07-23'),
  Ticker(symbol='HTZ', name='hertz'),
  Ticker(symbol='META', name='facebook', next_earnings='2024-07-24'),
  Ticker(symbol='MDB', name='mongodb', next_earnings='2024-08-30'),
  Ticker(symbol='MSFT', name='microsoft', next_earnings='2024-07-22'),
  Ticker(symbol='MSTR', name='Microstrategy', next_earnings='2024-07-30'),
  Ticker(symbol='NET', name='Cloudflare', next_earnings='2024-08-01'),
  Ticker(symbol='NVDA', name='nvidia', next_earnings='2024-08-21'),
  Ticker(symbol='OKTA', name='okta', next_earnings='2024-08-29'),
  Ticker(symbol='SHOP', name='Shopify', next_earnings='2024-08-07'),
  Ticker(symbol='SNAP', name='snapchat', next_earnings='2024-07-23'),
  Ticker(symbol='SQ', name='Square'),
  Ticker(symbol='SVOL', name='SVOL'),
  Ticker(symbol='TSLA', name='tesla', next_earnings='2024-07-16'),
  Ticker(symbol='TWLO', name='twilio', next_earnings='2024-08-13'),
  Ticker(symbol='TSM', name='TSM', next_earnings='2024-07-18'),
  Ticker(symbol='TXN', name='Texas Instruments', next_earnings='2024-07-23'),
  #Ticker(symbol='GME', name='Gamestop'),
]
