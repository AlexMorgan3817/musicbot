from yaml import load, dump
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

configuration = {}
def LOAD_CONFIGURATION(path):
	file = open(path)
	data = load(file.read(), Loader)
	file.close()
	return data

configuration = LOAD_CONFIGURATION("config/bot.yml")

def GetSetting(key, config = configuration):
	if(key in config):
		return config[key]

def SetSetting(key, value, config = configuration):
	if key in config:
		config[key] = value
