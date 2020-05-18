from discord.ext import commands
from riotwatcher import RiotWatcher
from decouple import config
import requests
import bs4
import discord

# Build contains methods for the -build {champion} command
# Example command: -build jinx
class Build(commands.Cog):

  # In addition to the discord bot instance
  # A RiotWatcher instance is used to pull data for get_champin_list()
  # Region is needed for riotwatcher's datadragon.champions() method
  def __init__(self, bot):
    self.bot = bot
    self.api = RiotWatcher(config('RIOT_API_KEY'))
    self.region = 'na1'

  # Returns the version string: '10.10.123456'
  def get_version(self):
    return self.api.data_dragon.versions_for_region(self.region)['v']

  # Returns a list of champion names for the current version: ['ahri', 'aatrox'...]
  def get_champion_list(self):
    champion_names = []
    version = self.get_version()
    champions = self.api.data_dragon.champions(version)

    # For each champion name, replace spaces and apostrophes and lowercase it.
    # Wukong is refered to as 'monkeyking' in the api, replace it.
    for champion in champions['data']:
      formatted_name = champion.replace(' ', '').replace("'", '').lower()
      if formatted_name == 'monkeyking':
        formatted_name = 'wukong'
      champion_names.append(formatted_name)
    return champion_names

  # Scrapes summoner spells from op.gg
  # Returns a dictionary. Example { 'flash': 'http://image_link.com' }
  def get_summoner_spells(self, document):
    images = document.select('.champion-overview__table--summonerspell td ul li img')[:2]
    summoner_spells = {}

    # Parse the summoner name from the images src
    # Remove the two slashes before the image src
    for i in images:
      src = i.attrs['src']
      name_index = src.find('Summoner')
      file_extension = src.find('.png')
      name = src[name_index + 8:file_extension].lower()
      summoner_spells[name] = src[2:file_extension + 4]
    
    return summoner_spells

  # Scrapes skill order from op.gg
  # Returns a dictionary. Example { 'Q': 'http://image_link.com' }
  # Since dictionaries maintain insertion order by default, the order of the keys
  # Is the order the skills should be chosen
  def get_skill_priority(self, document):
    images = document.select('.champion-stats__list__item img')[4:7]
    skill_priority = {}

    # Parse the skill letter from the image src
    # Remove the two slashes before the image src
    for i in images:
      file_extension = i.attrs['src'].find('.png')
      src = i.attrs['src'][2:file_extension + 4]
      letter = i.attrs['src'][file_extension - 1]
      skill_priority[letter] = src

    return skill_priority

  # Scrapes starting items from op.gg
  # Returns a dictionary. Example { '1234': 'http://image_link.com' }
  def get_starting_items(self, document):
    images = document.select('.champion-stats__list__item img')[7:9]
    starting_items = {}

    # Parse the item number from the image src
    # Remove the two slashes before the image src
    for i in images:
      start = i.attrs['src'].find('item/') + 5
      file_extension = i.attrs['src'].find('.png')
      item_number = i.attrs['src'][start:file_extension]
      src = i.attrs['src'][2:file_extension + 4]
      starting_items[item_number] = src

    return starting_items

  # Scrapes core items from op.gg
  # Returns a dictionary. Example { '1234': 'http://image_link.com' }
  def get_core_items(self, document):
    images = document.select('.champion-stats__list__item img')[11:14]
    core_items = {}

    # Parse the item number from the image src
    # Remove the two slashes before the image src
    for i in images:
      start = i.attrs['src'].find('item/') + 5
      file_extension = i.attrs['src'].find('.png')
      item_number = i.attrs['src'][start:file_extension]
      src = i.attrs['src'][2:file_extension + 4]
      core_items[item_number] = src

    return core_items

  # Scrapes boots from op.gg
  # Returns a dictionary. Example { '1234': 'http://image_link.com' }
  def get_boots(self, document):
    image = document.select('.champion-overview__row--first td ul li img')[7]
    
    # Parse the item number from the image src
    # Remove the two slashes before the image src
    start = image.attrs['src'].find('item/') + 5
    file_extension = image.attrs['src'].find('.png')
    item_number = image.attrs['src'][start:file_extension]
    src = image.attrs['src'][2:file_extension + 4]
    
    return { item_number : src }

  # Scrapes the data from u.gg using the champion argument
  # Returns a dictionary with all the data needed for the build
  def get_build(self, champion):
    # First get the document
    res = requests.get(f'https://na.op.gg/champion/{champion}')
    document = bs4.BeautifulSoup(res.text, features='html.parser')

    # Scrape the data
    summoner_spells = self.get_summoner_spells(document)
    skill_priority = self.get_skill_priority(document)
    starting_items = self.get_starting_items(document)
    core_items = self.get_core_items(document)
    boots = self.get_boots(document)
    
    build = {
      'spells': summoner_spells,
      'skills': skill_priority,
      'starting_items': starting_items,
      'core_items': core_items,
      'boots': boots
    }
    print(starting_items)
    return build

  # Returns the string link to the thumbnail of the champion
  def get_thumbnail(self, champion):
    names = {
      'drmundo': 'DrMundo',
      'jarvan': 'JarvanIV',
      'jarvan iv': 'JarvanIV',
      'kogmaw': 'KogMaw',
      'leesin': 'LeeSin',
      'masteryi': 'MasterYi',
      'missfortune': 'MissFortune',
      'wukong': 'MonkeyKing',
      'reksai': 'RekSai',
      'tahmkench': 'TahmKench',
      'twistedfate': 'TwistedFate',
      'xinzhao': 'XinZhao'
    }

    if champion in names:
      return f'http://ddragon.canisback.com/latest/img/champion/{names[champion]}.png'
    else:
      return f'http://ddragon.canisback.com/latest/img/champion/{champion.title()}.png'

  # Creates an embed with the build data
  # Returns a discord.Embed with the build data
  def create_build_embed(self, build, thumbnail):
    embed = discord.Embed(color=discord.Color(0xff0000),
                          title=f'Jinx Build For Patch {self.get_patch()[:4]}')
    embed.set_thumbnail(thumbnail)
    embed.add_field('Summoner Spells')


  # Returns an embed of the argument champion's most common build.
  # Data is sourced from u.gg
  @commands.command()
  async def build(self, ctx, *champion):
    # Remove spaces and apostrophes from champion name and lowercase it
    champion = ''.join(champion).replace("'", '').lower()
    # If the champion is valid, 
    # Get the build and thumbnail and pass to create_build_embed()
    if champion in self.get_champion_list():
      build = self.get_build(champion)
      thumbnail = self.get_thumbnail(champion)
    else:
      'Invalid champion'

    # Create the embed and send the message to the channel called
    #embed = self.create_build_embed(build, thumbnail)
    #ctx.message.channel.send(embed=embed)
