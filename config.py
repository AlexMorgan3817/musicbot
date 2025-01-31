from yaml import load, dump
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

configuration = {}
def LOAD_CONFIGURATION(path = "config/bot.yml"):
	file = open(path)
	data = load(file.read(), Loader)
	print(dump(data, Dumper=Dumper))
	file.close()
	return data

def SAVE_CONFIGURATION(path = "config/bot.yml", cfg = configuration):
	f = open(path)
	dump(cfg, f, Dumper=Dumper)
	f.close()

configuration = LOAD_CONFIGURATION()

def GetSetting(key, config = configuration):
	if(key in config):
		return config[key]

def SetSetting(key, value, config = configuration):
	if key in config:
		config[key] = value
