import re
from .sterling import sterling

class Archaic:
	DENOMINATIONS = [
		("guinea", 252),     # £1 1s
		("£", 240),          # 1 pound
		("crown", 60),       # 5 shillings
		("half-crown", 30),  # 2s6d
		("florin", 24),      # 2 shillings
		("shilling", 12),
		("sixpence", 6),
		("threepence", 3),
		("penny", 1),
		("halfpenny", 0.5),
		("farthing", 0.25),
	]

	NAME_MAP = {
		"guinea": "guinea",
		"guineas": "guinea",
		"£": "£",
		"pound": "£",
		"pounds": "£",
		"crown": "crown",
		"crowns": "crown",
		"half-crown": "half-crown",
		"half-crowns": "half-crown",
		"florin": "florin",
		"florins": "florin",
		"shilling": "shilling",
		"shillings": "shilling",
		"s": "shilling",
		"sixpence": "sixpence",
		"threepence": "threepence",
		"penny": "penny",
		"pennies": "penny",
		"d": "penny",  # the real cursed one
		"halfpenny": "halfpenny",
		"halfpence": "halfpenny",
		"farthing": "farthing",
		"farthings": "farthing",
	}

	VALUE_MAP = {name: worth for name, worth in DENOMINATIONS}

	@staticmethod
	def from_sterling(value: sterling) -> str:
		old_pence_total = float(value) * 240
		result = []
		for name, worth in Archaic.DENOMINATIONS:
			count, old_pence_total = divmod(old_pence_total, worth)
			count = int(count)
			if count:
				label = name if count == 1 else name + "s"
				result.append(f"{count} {label}")
		return ", ".join(result) if result else "0d"

	@staticmethod
	def to_sterling(string: str) -> sterling:
		# Handle compact forms like "10s6d" or "2/6"
		compact_pattern = re.findall(r"(\d+)([sd])", string)
		if compact_pattern:
			total = 0.0
			for count, denom_token in compact_pattern:
				denom = Archaic.NAME_MAP.get(denom_token)
				total += int(count) * Archaic.VALUE_MAP[denom]
			return sterling(total / 240)

		# Handle verbose forms
		tokens = re.split(r"[,\s]+", string.strip())
		total = 0.0
		i = 0
		while i < len(tokens):
			if tokens[i].isdigit():
				count = int(tokens[i])
				denom_token = tokens[i + 1].lower()
				denom = Archaic.NAME_MAP.get(denom_token)
				if denom is None:
					raise ValueError(f"Unknown denomination: {denom_token}")
				total += count * Archaic.VALUE_MAP[denom]
				i += 2
			else:
				i += 1
		return sterling(total / 240)