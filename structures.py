from discord.ext import commands
class PlayingData:
	ctx:commands.Context = None
	def __init__(self, _ctx, _path, _prt = None, _vlm = None):
		self.ctx  = _ctx
		self.path = _path
		self.prompt = _prt
		self.volume = _vlm
