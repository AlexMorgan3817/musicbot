import discord
from discord import *
from discord.ext import commands
from discord import FFmpegPCMAudio
import asyncio
import ffmpeg
from os.path import exists as fexist, isdir
from os import listdir, walk
import LnkParse3 as lps
from random import choice as pick

from config import GetSetting, SetSetting, SAVE_CONFIGURATION

from structures import *

I = discord.Intents.default()
I.message_content = True

bot:commands.Bot = commands.Bot(command_prefix = GetSetting('prefix'), intents = I)
loopingaudio = False
Queue:list = []
CurrentPlayingMusic:PlayingData = None
permited_extentions = ["mp3", "ogg", "flac", "lnk"]
listvariants = ["◈", "◍", "◰"]
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

async def Play(PD: PlayingData):
	def streamexhausted(_):
		global CurrentPlayingMusic
		global Queue
		global loopingaudio
		global skiplooping
		if skiplooping:
			print("Loop stopped.")
			skiplooping = False
			CurrentPlayingMusic = None
			return
		if not loopingaudio:
			if len(Queue):
				m = Queue.pop(0)
				print(f"{m.prompt}:{m.path}.")
				# await Play(m)
				asyncio.run_coroutine_threadsafe(Play(m), bot.loop)
			else:
				print(f"Stopped.")
				CurrentPlayingMusic = None
		else:
			print(f"New Loop.")
			CurrentPlayingMusic.ctx.voice_client.play(
				FFmpegPCMAudio(CurrentPlayingMusic.path), after=streamexhausted)
	global CurrentPlayingMusic
	VC = PD.ctx.voice_client
	if(CurrentPlayingMusic):
		stopPlaying(VC)
	CurrentPlayingMusic = PD
	VC.play(FFmpegPCMAudio(PD.path), after=streamexhausted)
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
	n:string = args[-1]

	needtoqueue:bool = True
	if "-f" in args:
		needtoqueue = False

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
		lnk_data:string = lps.lnk_file(f)
		j = lnk_data.get_json()["link_info"]
		p = j["local_base_path"] + j["common_path_suffix"]
		# if(isdir(p))
			
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
	root = './lib/'
	embedVar = discord.Embed(color=0x8833dd)
	title = ""
	if CurrentPlayingMusic:
		print(CurrentPlayingMusic.prompt)
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
	root = './lib/'
	embedVar = discord.Embed(color=0x8833dd)
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
	v = not GetSetting("whitelisted")
	SetSetting("whitelisted", v)
	await ctx.send(f"Bunker turned {'on' if v else 'off'}.")
@bot.command(pass_context = True)
async def DEBUG(ctx):
	ctx.voice_client.soundboard_sounds
# @bot.command(pass_context = True)
# async def hide(ctx):
# 	v = not GetSetting("hiden-path")
# 	SetSetting("hiden-path", v)
# 	await ctx.send(f"Hide {'on' if v else 'off'}.")

bot.run(GetSetting('token'))
# SAVE_CONFIGURATION()
# print("End.")
