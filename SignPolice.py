import os
import discord
import requests
import sys
import time

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

 # Gets token from .env
TOKEN = os.getenv('TESTTOKEN')
#TOKEN = os.getenv('TOKEN')

 # This requires some set up in the Discord Developer Portal
 # Without the members intent the bot can't see other users
intents = discord.Intents.default()
intents.members = True

Prefix = 'Public shaming of slackers by the :police_car: signpolice :police_car:\nList of slackers:'
Postfix = ''

raidingRoles = ["Officer", "Raider"]

bot = commands.Bot(command_prefix='!', intents = intents)

 # How to use:
 # Reply to the Raid-Helper event message with !signpolice
 # It takes a few seconds because the bot has to send an http request for each reaction-emote under the event

 # OLD WAY: (still usable using !signpoliceCSV [url])
 # The bot will download the CSV file generated by Raid-Helper
 # Get the link using:
 # !print 822243936173031464      <- remember to use the correct ID
 # Give the link as an argument
 
#@bot.command(name='getSignedListCsv')
def getSignedListCsv(url):
	try:
		# Make the request to the Raid-Helper CSV file, and prepare it for use
		resp = requests.get(url)
		
		# throw an http error if something went wrong
		resp.raise_for_status()
		respLines = resp.content.decode("utf8").split("\n")
		
		# Create Array of signed Players
		# These are just strings, not user objects
		signedPlayers = []
		for i in range(4, len(respLines)-1):
			Player = respLines[i].split(",")[2].lower()
			signedPlayers.append(Player)
			
		return signedPlayers
				
	except requests.exceptions.HTTPError as er:
		print(f'{er}')
		return False
	except ConnectionError:
		print(f'An connection error has occured')
		return False
	except Timeout:
		print(f'Connection timed out')
		return False


# Called when the bot spots a message (private or in a channel)
# Mainly here for debug purposes
@bot.event
async def on_message(message):
	# without this line other commands would fail to work
	await bot.process_commands(message)
	#print(
	#	f'{message.content}\n{message.reference}'
	#)
	#if message.reference != None:
	#	refMessage = await
	#	print(f'{message.reference.content}')

#@bot.command(name='testReply')
async def getSignedListReactions(context):
	# Testing
	ref = context.message.reference.message_id
	if ref != None:
		msg = await context.fetch_message(ref)
		repliers = []
		# Loop through all the reaction emotes
		for x in range(len(msg.reactions)):
			# Get all the users who used the emote
			user_list = [u for u in await msg.reactions[x].users().flatten() if u != bot.user]
			# Loop through all these users
			for y in range(len(user_list)):
				if not user_list[y].name.lower() in repliers:  # no duplicates please
					print(f'{user_list[y].name.lower()}')
					# I'm making this a list of strings so I don't need to rewrite the compareAndSnitch() function
					# This way I can keep in the CSV option as a backup, in case the reaction checking breaks
					# The CSV option is more accurate, but also a pain to use
					repliers.append(user_list[y].name.lower())
		# Debugging
		print(f'{repliers}')
		
		return repliers
		
	else:
		print(f'{ref}')
	await context.message.delete()
	

# Called when the Bot connects to discord
# Mostly for debug purposes
@bot.event
async def on_ready():
	print(f'{bot.user} has connected to Discord!')

	for guild in bot.guilds:
		print(
			f'-------------------------------------------------------------------------------------------\n'
			f'-------------------------------------------------------------------------------------------\n'
			f'{bot.user} is connected to the following guild:\n'
			f'{guild.name}(id: {guild.id})'
		)

# Get all the raiders
# Get all the players with officer OR Raider roles and throw them in a list
def get_members(context):
	raiders = [] # List of DiscordUser objects, NOT strings
	roles = [] # List of DiscoredRoles
	
	# Get the actual role objects, currently we only have the names as strings
	for y in range(0,len(raidingRoles)):
		role = discord.utils.find(
			lambda r: r.name == raidingRoles[y], context.guild.roles) # <--- might as well be wizardry to me
		roles.append(role)
	
	# For every User, check whether they posses any of the raidingRoles
	# raidingRoles are defined globally, at the top of this script
	for user in context.guild.members:
		print(f'Checking user: {user.name}')
		for raidrole in roles:
			if raidrole in user.roles:
				#await ctx.send(f"{user.mention} has the role {role.mention}")
				print(f"{user.name} has the role {raidrole.name}")
				raiders.append(user)
				
				# No duplicates please
				break 
	return raiders

async def compareAndSnitch(context, signedPlayers, raiders, prefix, postfix):
	PublicShameTargets = ''
	
	# Some debug info
	print('signed Players: \n')
	print(signedPlayers)
	print("\n\n\nExisting Raiders who are slacking:\n")
	
	# Check for every raider
	for raider in raiders:
		# Bots are superior to humans and thus can't be slackers
		if not raider.bot:
			if not raider.name.lower() in signedPlayers:
				PublicShameTargets += f'{raider.mention} '
				print(f'{raider.name} is a slacker')
	await context.send(f'{prefix}{PublicShameTargets}{postfix}')
	
	# Clean up
	await context.message.delete()

	
@bot.command(name='signpolice',help='Reply this command to a Raid-Helper Calender call out slackers\nFor custom shaming text type:\n!signpolice "[text before list]" "[text after list]"')
@commands.has_role("Officer") # Have to hardcode this sadly :(
async def signpolice(context, prefix=Prefix, postfix=Postfix):
	signedPlayers = await getSignedListReactions(context)
	if (signedPlayers == False or signedPlayers == None):
		print('An error has occured, quitting!')
		await context.message.delete()
		return
	raiders = get_members(context)
	
	await compareAndSnitch(context, signedPlayers, raiders, prefix, postfix)
	
# Handle Bachussus:
# I mean he's ganna try if he ever figures out how
@signpolice.error
async def signpolice_error(context, error):
	if isinstance(error, commands.MissingRole):
		await context.send(f'Only Officers can use this command\nWe\'re called Police Officers not Police Raiders :clown:')
	else:
		# A catch-all for when the other error handling has failed
		print(f'And error has occured: {error}')
		
	# Clean up
	await context.message.delete()

# Testing whether the bot has access to the guildlist		
@bot.command(name='testMemberAccess',help='Tests if the bot has the Members Intent special privilege')		
async def testMemberAccess(context):
	for member in context.guild.members: 
		print(f'{member.name}')
	
	# Clean up
	await context.message.delete()


# The old way of doing it
@bot.command(name='signpoliceCSV')
@commands.has_role("Officer") # Have to hardcode this sadly :(
async def signpoliceCSV(context,url):
	signedPlayers = getSignedListCsv(url)
	if (signedPlayers == False ):
		print('An error has occured, quitting!')
		await context.message.delete()
		return
	raiders = get_members(context)
	
	await compareAndSnitch(context, signedPlayers, raiders)	

# Handle Bachussus:
# I mean he's ganna try if he ever figures out how
@signpoliceCSV.error
async def signpolice_error(context, error):
	if isinstance(error, commands.MissingRole):
		await context.send(f'Only Officers can use this command\nWe\'re called Police Officers not Police Raiders :clown:')
	else:
		# A catch-all for when the other error handling has failed
		print(f'And error has occured: {error}')
		
	# Clean up
	await context.message.delete()
	
bot.run(TOKEN) 































