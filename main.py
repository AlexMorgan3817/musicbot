import discord
from discord import *
from discord.ext import commands
from discord import FFmpegPCMAudio
import ffmpeg
from os.path import exists as fexist
from os import listdir, walk
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
	if message.content[0] == GetSetting('prefix') and\
	   GetSetting("whitelisted") and not message.author.name in GetSetting("whitelist"):
		await message.channel.send(
			f"Sorry, but Master prohibbited to speak with strangers for today, dear {message.author.name}.")
		return
	splt = message.content.split(" ")
	splt[0] = splt[0].lower()
	message.content = " ".join(splt)
	await bot.process_commands(message)

def get_dirs(path = "./lib/"):
	dot = []
	for root, d_names, f_names in walk(path):
		dot += d_names
	return dot

@bot.command(pass_context = True)
async def play(ctx):
	if not ctx.voice_client:
		if ctx.author.voice:
			await ctx.message.author.voice.channel.connect()
		else:
			await ctx.send("Join channel and i will follow you.")
			return
	n = ctx.message.content[6:]
	# if n.find("\\") != -1 or n.find("/") != -1:
	# 	await ctx.send("Sorry, but Master told me not to let you go from ./lib/.")
	# 	return
	p = f'./lib/{n}'
	dirs = get_dirs('./lib/')
	files = []
	for i in listdir("./lib/"):
		files.append(f"./lib/{i}")
	if len(dirs) != 0:
		for j in dirs:
			for i in listdir(f"./lib/{j}"):
				files.append(f"./lib/{j}/{i}")
	# print(dirs)
	# print(files)
	if not fexist(p):
		for i in files:
			splt_0 = i.split("/")
			splt_1 = splt_0[-1].split(".")
			if splt_1[0].startswith(n):
				p = i
				n = splt_1[0]
				break
		if not fexist(p):
			#not found? => Seach substrings
			for i in files:
				splt_0 = i.split("/")
				splt_1 = splt_0[-1].split(".")
				if splt_1[0].find(n) != -1 or splt_1[0].lower().find(n.lower()) != -1:
					p = i
					n = splt_1[0]
					break

			#💀
			if not fexist(p):
				await ctx.send(f"The tone {p} is not found.")
				return

	ext = p.split(".")
	if ext[-1] == "lnk":
		f = open(p, 'rb')
		lnk = lps.lnk_file(f)
		j = lnk.get_json()["link_info"]
		p = j["local_base_path"] + j["common_path_suffix"]
		print(p)
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
			dot.append(f'### {sp[0]}/')
			file_list = getFilesInFolder(root + i)
			files = ""
			for i in range(0, len(file_list)-1):
				files += file_list[i] + ", "
				# dot.append(f'\t{i}')
			files += file_list[-1]
			dot.append(files)
			continue
		if sp[-1] in permited_extentions:
			dot.append(i)
		else:
			dot.append("~~" + i + "~~")
	print(dot)
	await ctx.send("\n".join(dot))

@bot.command(pass_context = True)
async def bunker(ctx):
	v = not GetSetting("whitelisted")
	SetSetting("whitelisted", v)
	await ctx.send(f"Bunker turned {'on' if v else 'off'}.")

bot.run(GetSetting('token'))
