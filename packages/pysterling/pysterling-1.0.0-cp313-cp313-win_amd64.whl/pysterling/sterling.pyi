import typing
ConvertibleToSterling: typing.TypeAlias = str | typing.SupportsInt | float
class sterling:
	'''sterling(x) -> sterling pounds + pence

	Convert a number to Sterling Pounds and Pence, or return £0.00 if no arguments
	are given. If x is a number, return x.__sterling__() if defined, else int/float.

	If x is not a number, then x must be a string representing a sterling literal.  
	The literal must be prefaced with £ and have a period as a delimiter.

	>>> sterling("£1.00")
	£1.00
	'''
	def __new__(cls, x: ConvertibleToSterling = ..., /) -> typing.Self: ...