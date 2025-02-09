from yaml import load, dump
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

class Config():
	values:dict = {}
	path:str = None
	def __init__(self, _path:str = None):
		if _path:
			self.path = _path
			self.values = self.Load(_path)

	def Set(self, key:str, value):
		self.values[key] = value

	def Get(self, key:str):
		if self.values[key]:
			return self.values[key]

	def Load(self, _path):
		file = open(_path)
		data = load(file.read(), Loader)
		print(dump(data, Dumper=Dumper))
		file.close()
		return data
	
	def Save(self, path:str):
		f = open(path)
		dump(self.values, f, Dumper=Dumper)
		f.close()

