import math
import typing

class array: ...

class arrayIterator:
	def __init__(self, array):
		self.array = array
		self.nextpos = 0
	def __iter__(self):
		return self
	def __next__(self):
		if self.array is None or self.nextpos >= len(self.array._values):
			self.array = None
			raise StopIteration
		value = self.array._values[self.nextpos]
		self.nextpos += 1
		return value

class array:

	def __init__(self, values, _type=None):
		self._values = values

		if _type is None and len(self._values): self._type = type(self._values[0])
		elif len(self._values): self._type = _type
		else: raise AttributeError("Either values or a type must be specified.")

		for v in self._values:
			v = self._type(v)

	def mean(self):
		return sum(self._values) / len(self._values)

	def stddev(self):
		return self.variance()**0.5

	def variance(self):
		E = self.mean()
		return sum([(x - E)**2 for x in self]) / len(self)

	@staticmethod
	def covariance(a, b):
		if len(a) != len(b): raise AttributeError("Length of arrays must match.")
		return sum((a - a.mean()) * (b - b.mean()))

	@staticmethod
	def pcc(a, b):
		return array.covariance(a, b) / (a.variance()*len(a) * b.variance()*len(b))**0.5

	def reverse(self):
		self._values.reverse()

	def reversed(self):
		values = self._values.copy()
		values.reverse()
		return values

	def copy(self):
		return array(self._values.copy(), self._type)


	def __iter__(self):
		return arrayIterator(self)

	def __getitem__(self, i: int):
		return self._values[i]
	def __setitem__(self, i: int, v):
		self._values[i] = v

	def __len__(self) -> int:
		return len(self._values)

	def __trunc__(a) -> array:
		return array([math.trunc(v) for v in a], int)

	def __ceil__(a) -> array:
		return array([math.ceil(v) for v in a], int)

	def __floor__(a) -> array:
		return array([math.floor(v) for v in a], int)

	def __round__(a, n) -> array:
		return array([round(v, n) for v in a])

	def __abs__(a) -> array:
		return array([abs(v) for v in a])

	def __neg__(a) -> array:
		return array([-v for v in a])

	def __add__(a, b:[array, float, int]) -> array:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			return array([a[i] + b[i] for i in range(len(a))])
		else:
			return array([a[i] + b for i in range(len(a))])

	def __sub__(a, b:[array, float, int]) -> array:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			return array([a[i] - b[i] for i in range(len(a))])
		else:
			return array([a[i] - b for i in range(len(a))])

	def __mul__(a, b:[array, float, int]) -> array:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			return array([a[i] * b[i] for i in range(len(a))])
		else:
			return array([a[i] * b for i in range(len(a))])

	def __floordiv__(a, b:[array, float, int]) -> array:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			return array([a[i] // b[i] for i in range(len(a))])
		else:
			return array([a[i] / b for i in range(len(a))])

	def __truediv__(a, b:[array, float, int]) -> array:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			return array([a[i] / b[i] for i in range(len(a))])
		else:
			return array([a[i] / b for i in range(len(a))])

	def __mod__(a, b:[array, float, int]) -> array:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			return array([a[i] % b[i] for i in range(len(a))])
		else:
			return array([a[i] % b for i in range(len(a))])

	def __divmod__(a, b:[array, float, int]) -> tuple[array, array]:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			div = []
			mod = []
			for i in range(len(a)):
				div.append(a[i] // b[i])
				mod.append(a[i] % b[i])
			return (array(div), array(mod))
		else:
			div = []
			mod = []
			for i in range(len(a)):
				div.append(a[i] // b)
				mod.append(a[i] % b)
			return (array(div), array(mod))
	
	def __pow__(a, b:[array, float, int]) -> array:
		if type(b) is array:
			if len(a) != len(b): raise AttributeError("Length of arrays must match.")
			return array([a[i] * b[i] for i in range(len(a))])
		else:
			return array([a[i] * b for i in range(len(a))])

	def __str__(a) -> str:
		return f"array : [\n\t{',\n\t'.join([str(v) for v in a])}\n]"

	def __repr__(a) -> str:
		return f"array([{', '.join([str(v) for v in a])}], {a._type})"

	def __eq__(a, b: array) -> bool:
		if len(a) != len(b): raise AttributeError("Length of arrays must match.")
		return False not in [a[i] == b[i] for i in range(len(a))]

	def __ne__(a, b: array) -> bool:
		if len(a) != len(b): raise AttributeError("Length of arrays must match.")
		return True not in [a[i] == b[i] for i in range(len(a))]

