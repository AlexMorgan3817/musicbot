import asyncio
from os.path import exists as fexist, isdir
from os import listdir, walk, system as shell
from sys import argv
from random import choice as pick
import discord
from discord import FFmpegPCMAudio, Message
from discord.ext import commands
import LnkParse3 as lps

import config
from config import Config

from structures import PlayingData
cfg_path = "config/bot.yml"
print(argv)
if "-cfg" in argv:
	idx = argv.index("-cfg")
	cfg_path = argv[idx+1]

cfg:Config = Config(cfg_path)
lib_root:str = cfg.Get("lib_path")
name:str = cfg.Get('name')
color:str = cfg.Get('color')#0x8833dd
shell(f"title {name}")


I = discord.Intents.default()
I.message_content = True
bot:commands.Bot = commands.Bot(command_prefix = cfg.Get('prefix'), intents = I)
loopingaudio = False
Queue:list = []
CurrentPlayingMusic:PlayingData = None
permited_extentions = ["mp3", "ogg", "flac", "lnk"]
listvariants = ["◈", "◍", "◰"]
skiplooping = False
VolumeMult:float = 1


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
	if message.content[0] == cfg.Get('prefix') and\
	   cfg.Get("whitelisted") and not message.author.name in cfg.Get("whitelist"):
		await message.channel.send(
			f"Sorry, but Master prohibbited to speak with strangers for today, dear {message.author.name}.")
		return
	splt = message.content.split(" ")
	splt[0] = splt[0].lower()
	message.content = " ".join(splt)
	await bot.process_commands(message)

def get_dirs(path = lib_root):
	dot = []
	for root, d_names, f_names in walk(path):
		dot += d_names
	return dot

async def Play(PD: PlayingData):
	def streamexhausted(_):
		global CurrentPlayingMusic, Queue, loopingaudio, skiplooping
		if skiplooping:
			print("Loop stopped.")
			skiplooping = False
			CurrentPlayingMusic = None
			return
		if not loopingaudio:
			if len(Queue):
				m = Queue.pop(0)
				asyncio.run_coroutine_threadsafe(Play(m), bot.loop)
			else:
				print(f"Stopped.")
				CurrentPlayingMusic = None
		else:
			print(f"New Loop.")
			asyncio.run_coroutine_threadsafe(Play(CurrentPlayingMusic), bot.loop)
			# CurrentPlayingMusic.ctx.voice_client.play(
			# 	FFmpegPCMAudio(CurrentPlayingMusic.path), after=streamexhausted)
	global CurrentPlayingMusic, VolumeMult
	VC = PD.ctx.voice_client
	if(CurrentPlayingMusic):
		stopPlaying(VC)
	CurrentPlayingMusic = PD
	VC.play(FFmpegPCMAudio(PD.path), after=streamexhausted)
	VC.source = discord.PCMVolumeTransformer(VC.source, volume=VolumeMult)
	await bot.change_presence(
		activity=discord.Activity(
			type=discord.ActivityType.listening,
			name=PD.prompt))

@bot.command(pass_context = True)
async def play(ctx):
	if not ctx.voice_client:
		if ctx.author.voice:
			await ctx.message.author.voice.channel.connect()
		else:
			await ctx.send("Join channel and i will follow you.")
			return
	args = ctx.message.content.split(" ")[1:]
	#Path Arg

	needtoqueue:bool = True
	idx_to_cut:int = 0
	if args[0] == "-f":
		needtoqueue = False
		idx_to_cut:int = 1
	n:str = " ".join(args[idx_to_cut:])

	p = f'{lib_root}/{n}'
	dirs = get_dirs(lib_root + "/")
	files = []
	for i in listdir(lib_root + "/"):
		files.append(f"{lib_root}/{i}")
	if len(dirs) != 0:
		for j in dirs:
			for i in listdir(f"{lib_root}/{j}"):
				files.append(f"{lib_root}/{j}/{i}")
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
		lnk_data:str = lps.lnk_file(f)
		j = lnk_data.get_json()["link_info"]
		p = j["local_base_path"] + j["common_path_suffix"]	
		print(p)
		f.close()
	global CurrentPlayingMusic
	if CurrentPlayingMusic:
		if needtoqueue:
			global Queue
			Queue.append(PlayingData(ctx, p, n))
			await ctx.send("Queued " + n)
			return
		else:
			stopPlaying(ctx.voice_client)
	await ctx.send("Playing " + n)
	await Play(PlayingData(ctx, p, n))


@bot.command()
async def loop(ctx):
	global loopingaudio
	loopingaudio = not loopingaudio
	await ctx.send(f"Now we are {'' if loopingaudio else 'not '}looping.")

def stopPlaying(vc):
	global skiplooping
	skiplooping = True
	CurrentPlayingMusic = None
	vc.stop()

async def Resume(ctx):
	if len(Queue) == 0:
		return False
	await Play(Queue.pop(0))
	return True

@bot.command() 
async def resume(ctx):
	if await Resume(ctx):
		return
	await ctx.send(f"Q is empty.")

@bot.command()
async def stop(ctx):
	if ctx.voice_client:
		stopPlaying(ctx.voice_client)
		await ctx.send("Stopped")

@bot.command()
async def skip(ctx):
	if ctx.voice_client:
		stopPlaying(ctx.voice_client)
		if len(Queue):
			await Resume(ctx)

@bot.command(pass_context = True)
async def join(ctx):
	if ctx.author.voice:
		if(ctx.voice_client):
			await ctx.voice_client.disconnect()
		await ctx.message.author.voice.channel.connect()
	else:
		await ctx.send("Join channel and i will follow.")

@bot.command(pass_context = True)
async def leave(ctx):
	if ctx.voice_client:
		await ctx.voice_client.disconnect()
	else:
		await ctx.send("I am not in the voice channel.")
class QueueView(discord.ui.View):
	# def __init__(self):
	# 	super().__init__()
	pass
	# @discord.ui.button(label=">", custom_id="resume", style=discord.ButtonStyle.primary)
	# async def resume_button(self, button: discord.ui.Button, interaction: discord.Interaction):
	# 	resume(interaction)
	# @discord.ui.button(label="⟳", custom_id="refresh", style=discord.ButtonStyle.primary)
	# async def refresh_button(self, button: discord.ui.Button, interaction: discord.Interaction):
	# 	q(interaction)

	# @discord.ui.button(label=">>", custom_id="skip", style=discord.ButtonStyle.primary)
	# async def skip_button(self, button: discord.ui.Button, interaction: discord.Interaction):
	# 	skip(interaction)
@bot.command(pass_context = True)
async def q(ctx):
	embedVar = discord.Embed(color=color)
	title = ""
	if CurrentPlayingMusic:
		title += " " + CurrentPlayingMusic.prompt + " is playing."
	if len(Queue) == 0:
		embedVar.add_field(name=title, value = "Queue is empty.", inline=True)
	else:
		res = ''
		idx:int = 0
		l:int = len(listvariants)
		for pd in Queue: #PlayingData
			res += listvariants[idx % l] + " " + pd.prompt + "\n"
			idx += 1
		embedVar.add_field(name=title, value=res, inline=False)
	await ctx.send(embed=embedVar, view=QueueView())

@bot.command(pass_context = True,
	brief="Shows files available.",
	description="Shows files on server available for play.")
async def lib(ctx):
	root = lib_root + "/"
	embedVar = discord.Embed(color=color)
	root_dir = []
	for i in listdir(root):
		sp = i.split(".")
		if len(sp) == 1: # dir
			file_list = getFilesInFolder(root + i)
			res = []
			for f in file_list:
				s = f.split(".")
				res.append(".".join(s[:-1]))
			embedVar.add_field(name=i, value="; ".join(res), inline=False)
		else:
			if sp[-1] in permited_extentions:
				root_dir.append(".".join(sp[:-1]))
	embedVar.add_field(name="./", value="; ".join(root_dir), inline=False)
	await ctx.send(embed=embedVar)

@bot.command(pass_context = True)
async def bunker(ctx):
	v = not cfg.Get("whitelisted")
	cfg.Set("whitelisted", v)
	await ctx.send(f"Bunker turned {'on' if v else 'off'}.")

@bot.command(pass_context = True)
async def DEBUG(ctx):
	ctx.voice_client.soundboard_sounds
# @bot.command(pass_context = True)
# async def hide(ctx):
# 	v = not Get("hiden-path")
# 	Get("hiden-path", v)
# 	await ctx.send(f"Hide {'on' if v else 'off'}.")
@bot.command(pass_context = True)
async def vol(ctx:commands.Context):
	global VolumeMult
	args = ctx.message.content.split(" ")
	if len(args) < 2:
		await ctx.send(f"Громкость: {VolumeMult}.")
		return
	if not ctx.voice_client:
		await ctx.send(f"Я не слушаю.")
		return
	if not ctx.voice_client.source:
		await ctx.send(f"Ничего не играет.")
		return
	volume:int = float(args[1])
	if not volume: return
	VolumeMult *= volume
	ctx.voice_client.source = discord.PCMVolumeTransformer(ctx.voice_client.source, volume=volume)
	await ctx.send(f"Новая громкость: {VolumeMult}.")

bot.run(cfg.Get('token'))
# SAVE_CONFIGURATION()
# print("End.")
