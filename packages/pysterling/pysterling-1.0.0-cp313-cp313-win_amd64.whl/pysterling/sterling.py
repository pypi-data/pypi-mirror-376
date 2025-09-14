from typing import TypeAlias, SupportsInt, Self, SupportsIndex, Literal
import numbers



ConvertibleToSterling: TypeAlias = str | SupportsInt | float

class sterling(numbers.Number):
	'''sterling(x) -> sterling pounds + pence

	Convert a number to Sterling Pounds and Pence, or return £0.00 if no arguments
	are given. If x is a number, return x.__sterling__() if defined, else int/float.

	If x is not a number, then x must be a string representing a sterling literal.  
	The literal must be prefaced with £ and have a period as a delimiter.

	>>> sterling("£1.00")
	£1.00
	'''

	__slots__ = ("_pence",)

	def __new__(cls, x: ConvertibleToSterling = 0, /) -> Self:
		this = super().__new__(cls)

		if isinstance(x, sterling):
			this._pence = x._pence
			return this

		if isinstance(x, str):
			x = x.strip().lstrip("£")
			pounds, _, pence = x.partition(".")
			this._pence = int(pounds) * 100 + int(pence.ljust(2, "0")[:2])
		else:
			val = float(x)
			this._pence = int(round(val * 100))

		return this

	def __sterling__(self) -> int:
		return self._pence

	def __int__(self) -> int:
		return self._pence // 100

	def __float__(self) -> float:
		return self._pence / 100

	def __str__(self) -> str:
		pounds, pence = divmod(self._pence, 100)
		return f"£{pounds}.{pence:02d}"

	def __repr__(self) -> str:
		return f"sterling('{self}')"

	# ---------- arithmetic ----------
	def __add__(self, other: ConvertibleToSterling) -> Self:
		return sterling.from_pence(self._pence + sterling(other)._pence)

	def __sub__(self, other: ConvertibleToSterling) -> Self:
		return sterling.from_pence(self._pence - sterling(other)._pence)

	def __mul__(self, other: SupportsInt | float) -> Self:
		val = float(other)
		return sterling.from_pence(int(round(self._pence * val)))

	__rmul__ = __mul__

	def __truediv__(self, other: ConvertibleToSterling | float) -> Self | float:
		if isinstance(other, sterling):
			if other._pence == 0:
				raise ZeroDivisionError("division by zero sterling")
			return self._pence / other._pence
		val = float(other)
		if val == 0:
			raise ZeroDivisionError("division by zero")
		return sterling.from_pence(int(round(self._pence / val)))

	def __neg__(self) -> Self:
		return sterling.from_pence(-self._pence)

	def __abs__(self) -> Self:
		return sterling.from_pence(abs(self._pence))

	# ---------- comparisons ----------
	def __eq__(self, other: object) -> bool:
		if isinstance(other, sterling):
			return self._pence == other._pence
		return NotImplemented

	def __lt__(self, other: ConvertibleToSterling) -> bool:
		return self._pence < sterling(other)._pence

	def __le__(self, other: ConvertibleToSterling) -> bool:
		return self._pence <= sterling(other)._pence

	def __gt__(self, other: ConvertibleToSterling) -> bool:
		return self._pence > sterling(other)._pence

	def __ge__(self, other: ConvertibleToSterling) -> bool:
		return self._pence >= sterling(other)._pence

	@classmethod
	def from_pence(cls, pence: int) -> Self:
		obj = super().__new__(cls)
		obj._pence = pence
		return obj

	def to_bytes(self, *, byteorder: Literal["little", "big"] = "big") -> bytes:
		'''56.8 fixed point representation'''
		# Value in hundredths of a pound -> scaled to 256ths
		scaled = round((self._pence / 100) * 256)
		# Make sure it fits into 56+8 = 64 bits
		if scaled.bit_length() > 64:
			raise OverflowError("sterling value too large for 56.8 fixed point")
		return scaled.to_bytes(8, byteorder)

	def from_bytes(data: bytes, *, byteorder: Literal["little", "big"] = "big") -> "sterling":
		scaled = int.from_bytes(data, byteorder)
		# reverse the scaling (back to pennies)
		pounds_float = scaled / 256
		pence = int(round(pounds_float * 100))
		return sterling.from_pence(pence)