from .sterling import sterling

class VAT:
	def __init__(self, base: sterling, rate: int = 20) -> None:
		self.base = sterling(base)
		self.rate = rate
		self._fraction = self.rate / 100

		self.tax = self.base * self._fraction
		self.gross = self.base + self.tax

	def __iter__(self):
		yield self.tax
		yield self.gross

	def __repr__(self):
		return f"VAT(base={self.base}, rate={self.rate}%) -> (tax={self.tax}, gross={self.gross})"