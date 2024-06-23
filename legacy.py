
def cache():
  def decorator(func):
    def wrapper(*args, **kwargs):
      file_name = func.__name__ + '_' + '-'.join(args) + '.pkl'
      if os.path.exists(file_name):
        # If the pickle file exists, load the cached result
        with open(file_name, 'rb') as file:
          result = pickle.load(file)
      else:
        # If the file doesn't exist, call the function and cache the result
        result = func(*args, **kwargs)
        with open(file_name, 'wb') as file:
          pickle.dump(result, file)
      return result
    return wrapper
  return decorator


#@cache
def fetch_raw_pe(symbol, company):
  url = f'https://www.macrotrends.net/stocks/charts/{symbol}/{company}/pe-ratio'
  return fetch_raw_historical(url)


def fetch_raw_pfcf(symbol, company):
  url = f'https://www.macrotrends.net/stocks/charts/{symbol}/{company}/price-fcf'
  return fetch_raw_historical(url)


def fetch_raw_historical(url):

  headers = {
      'User-Agent': (
          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
          '(KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
      )
  }
  resp = requests.get(url, headers=headers)

  data = pd.read_html(resp.text, skiprows=1)
  return data[0]


def graph_historical_pe(symbol, company, start_date=None, ax=None):
  column_names = ['Date', 'Price', 'EPS', 'PE']
  data = fetch_raw_pe(symbol, company)
  data.columns = column_names

  date = data['Date'].apply(pd.to_datetime)
  pe = data['PE'].apply(pd.to_numeric)
  pe_mean = round(pe.mean(), 2)

  print('Last earnings date:', date.iloc[0])
  print('Last earnings PE:', pe.iloc[0])
  print('Historical mean PE:', pe_mean)

  if ax:
    graph_historical(date.tolist(), pe.tolist(), pe_mean, symbol, ax)


def graph_historical(x, y, mean, title, ax):
  ax.set_title(title)
  ax.plot(x, y)
  ax.plot(x, [mean] * len(x), color='r', linestyle='--')

