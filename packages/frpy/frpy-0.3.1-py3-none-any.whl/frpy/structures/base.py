from json import dumps

class Base:
	def dict(self, seen=None):
		if seen is None:
			seen = set()

		if id(self) in seen:
			return f'<{self.__class__.__name__} circular>'
			# return None

		seen.add(id(self))

		result = {}
		for key, value in self.__dict__.items():
			if isinstance(value, Base):
				result[key] = value.dict(seen)
			elif isinstance(value, list):
				result[key] = [v.dict(seen) if isinstance(v, Base) else v for v in value]
			elif isinstance(value, dict):
				result[key] = {k: v.dict(seen) if isinstance(v, Base) else v for k, v in value.items()}
			else:
				result[key] = value

		return result

	def json(self, pretty=True, **kwargs):
		indent = kwargs.get('indent', 4 if pretty else None)
		if 'pretty' in kwargs:
			indent = 4 if kwargs['pretty'] else None

		raw = self.dict()
		if indent:
			return dumps(raw, ensure_ascii=False, indent=indent)

		return dumps(raw, ensure_ascii=False)