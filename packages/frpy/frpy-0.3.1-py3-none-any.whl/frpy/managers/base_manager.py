from ..structures.base import Base
from ..utils.map import Map

class BaseManager(Base):
	cache = Map()
	def __init__(self, parent):
		self.client = parent