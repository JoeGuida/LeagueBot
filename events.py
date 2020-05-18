from discord.ext import commands
import asyncio

class Events(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command(name='q')
  async def _quit(self, ctx):
    await asyncio.sleep(1)
    await self.bot.logout()

  @commands.Cog.listener()
  async def on_message(self, message):
    if message.content[0] == '-':
      await message.delete()
