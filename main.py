import discord
from discord import *
from discord.ext import commands
from discord import FFmpegPCMAudio
import ffmpeg
from os.path import exists as fexist
from os import listdir
import LnkParse3 as lps

from config import GetSetting, SetSetting

I = discord.Intents.default()
I.message_content = True

class playing:
	def __init__(self, _ctx, _path):
		self.ctx  = _ctx
		self.path = _path

bot:commands.Bot = commands.Bot(command_prefix = GetSetting('prefix'), intents = I)
loopingaudio = True
CurrentPlayingMusic:playing = None
permited_extentions = ["mp3", "ogg", "flac", "lnk"]

skiplooping = False

def getFilesInFolder(path, recursive = False):
	dot = []
	for i in listdir(path):
		sp = i.split(".")
		if len(sp) == 1:
			dot.append(f'{path}/{sp[0]}/')
			continue
		dot.append(i)
	return dot

@bot.event
async def on_ready():
	print("Loaded")
@bot.event
async def on_message(message:Message):
	print(f'Message from [{message.author}]:{message.content}')
	if message.author == bot.user:
		return
	if GetSetting("whitelisted") and not message.author.name in GetSetting("whitelist"):
		await message.channel.send(
			f"Sorry, but Master prohibbited to speak with strangers for today, dear {message.author.name}.")
		return
	splt = message.content.split(" ")
	splt[0] = splt[0].lower()
	message.content = " ".join(splt)
	await bot.process_commands(message)
@bot.command(pass_context = True)
async def play(ctx):
	if not ctx.voice_client:
		if ctx.author.voice:
			await ctx.message.author.voice.channel.connect()
		else:
			await ctx.send("Join channel and i will follow you.")
			return
	n = ctx.message.content[6:]
	if n.find("\\") != -1 or n.find("/") != -1:
		await ctx.send("Sorry, but Master told me not to let you go from ./lib/.")
		return
	p = f'./lib/{n}'
	if not fexist(p):
		for i in listdir("./lib/"):
			splt = i.split(".")
			if splt[0].startswith(n):
				p = './lib/' + i
				n = splt[0]
				break
		if not fexist(p):
			#not found? => Seach substrings
			for i in listdir("./lib/"):
				splt = i.split(".")
				if splt[0].find(n) != -1 or splt[0].lower().find(n.lower()) != -1:
					p = './lib/' + i
					n = splt[0]
					break
			#💀
			if not fexist(p):
				await ctx.send("The tone is not found.")
				return

	ext = p.split(".")
	if ext[-1] == "lnk":
		f = open(p, 'rb')
		lnk = lps.lnk_file(f)
		p = lnk.get_json()["link_info"]["local_base_path"]
		f.close()
	global CurrentPlayingMusic
	if CurrentPlayingMusic:
		stopPlaying(ctx)
	await ctx.send("Playing " + n)
	CurrentPlayingMusic = playing(ctx, p)
	ctx.voice_client.play(FFmpegPCMAudio(p), after=streamexhausted)
	await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=n))

def streamexhausted(_):
	global CurrentPlayingMusic
	global loopingaudio
	global skiplooping
	if loopingaudio and not skiplooping:
		CurrentPlayingMusic.ctx.voice_client.play(
			FFmpegPCMAudio(CurrentPlayingMusic.path),
			after=streamexhausted
		)
	else:
		skiplooping = False
		CurrentPlayingMusic = None
@bot.command(pass_context = True)
async def loop(ctx):
	global loopingaudio
	loopingaudio = not loopingaudio
	await ctx.send(f"Now we are {'' if loopingaudio else 'not '}looping.")
def stopPlaying(ctx):
	global skiplooping
	skiplooping = True
	ctx.voice_client.stop()
@bot.command()
async def stop(ctx):
	if ctx.voice_client:
		stopPlaying(ctx)
		await ctx.send("Stopped")
@bot.command(pass_context = True)
async def join(ctx):
	if ctx.author.voice:
		await ctx.message.author.voice.channel.connect()
	else:
		await ctx.send("Join channel and i will follow.")
@bot.command(pass_context = True)
async def leave(ctx):
	if ctx.voice_client:
		await ctx.voice_client.disconnect()
	else:
		await ctx.send("I am not in the voice channel.")
@bot.command(pass_context = True)
async def lib(ctx):
	dot = []
	root = './lib/'
	for i in listdir(root):
		sp = i.split(".")
		if len(sp) == 1:
			dot.append(f'{sp[0]}/')
			for i in getFilesInFolder(root + i):
				dot.append(f'\t{i}')
			continue
		if sp[-1] in permited_extentions:
			dot.append(sp[0])
		else:
			dot.append("~~" + sp[0] + "~~")
	print(dot)
	await ctx.send("\n".join(dot))
@bot.command(pass_context = True)
async def bunker(ctx):
	v = not GetSetting("whitelisted")
	SetSetting("whitelisted", v)
	await ctx.send(f"Bunker turned {'on' if v else 'off'}.")

bot.run(GetSetting('token'))

