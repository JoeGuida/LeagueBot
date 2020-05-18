from discord.ext import commands
from decouple import config
from events import Events
from build import Build

# Create the bot instance
bot = commands.Bot(command_prefix='-')

# Add Cogs
bot.add_cog(Events(bot))
bot.add_cog(Build(bot))

# Run the bot
bot.run(config('DISCORD_TOKEN'))