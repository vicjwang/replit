

class Signal:
  def __init__(self, price_model, *args, weight=1, **kwargs):
    self.price_model = price_model
    self.weight = weight


class SupportSignal(Signal):

  def compute_edge(self, row, max_proba):
    price = self.price_model.get_latest_price()
    return self.weight * max_proba * (price - self.support_price) / (price - row['strike'])


class MovingAverageSupportSignal(SupportSignal):
  def __init__(self, n, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.n = n

  def __str__(self):
    return "{}_ma_edge".format(self.n)

  def compute_edge(self, *args):
    self.support_price = self.price_model.get_ma(self.n)
    return super().compute_edge(*args)
