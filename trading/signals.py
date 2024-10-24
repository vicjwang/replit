from utils import compute_cdf


class Signal:
  def __init__(self, *args, weight=1, **kwargs):
    self.weight = weight


class SupportSignal(Signal):

  def __str__(self):
    raise NotImplementedError

  def validate_conditions(self, price, strike):
    return price > self.support_price and strike < self.support_price

  def compute_edge(self, row, max_proba, **kwargs):
    price = kwargs['price_model'].get_latest_price()
    strike = row['strike']
    if not self.validate_conditions(price, strike):
      return 0
    return self.weight * max_proba * (price - self.support_price) / (price - strike)


class MovingAverageSupportSignal(SupportSignal):
  def __init__(self, n, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.n = n

  def __str__(self):
    return "{}_ma_edge".format(self.n)

  def compute_edge(self, row, max_proba, **kwargs):
    self.support_price = kwargs['price_model'].get_ma(self.n)
    return super().compute_edge(row, max_proba, **kwargs)


class FiftyTwoLowSupportSignal(SupportSignal):
  def __str__(self):
    return '52_low_edge'

  def compute_edge(self, row, max_proba, **kwargs):
    self.support_price = kwargs['price_model'].get_52_low()
    return super().compute_edge(row, max_proba, **kwargs)


class DeltaSignal(Signal):

  def __str__(self):
    return 'delta_edge'

  def compute_edge(self, row, max_proba, **kwargs):
    lose_proba = 1 - kwargs['win_proba']
    delta = abs(row['delta'])
    return max_proba * (1 - lose_proba / delta) if lose_proba < delta else 0


class MoveSignal(Signal):
  def __str__(self):
    return 'move_edge'

  def compute_edge(self, row, max_proba, **kwargs):
    # Assume option type = put.
    price_model = kwargs['price_model']
    move = price_model.get_latest_change()
    sigma = price_model.get_daily_stdev()
    zscore = move / sigma
    return max_proba * (0.5 - compute_cdf(zscore)) / 0.5 if move < 0 else 0
