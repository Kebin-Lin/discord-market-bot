# Discord Marketplace Bot
<div align="center">
  <img src="https://i.imgur.com/5uBevDC.png" height="200" align="center"/>
</div>

## Introduction
This is a Discord bot to facilitate buying/selling items for online games. It is formatted to run on Heroku and requires access to a PostgreSQL database. It is
built to support multiple isolated "markets" and includes optional moderation tools for markets created by a certain user. The specific market used is set by
channel, allowing a server to have multiple channels for different markets, for example if there are different currencies used or goods sold. The bot can also be
set to a market in DMs to avoid cluttering server chat logs. Searching for items involves simplified SQL queries, but search results use a reaction-based
interface. Users can also have the bot ping the seller of an item to notify them of their interest.

## Setup
1. Pull a copy of this repository to Heroku.
2. In the Heroku project, under Settings > Config Vars, add a key named DATABASE_URL and set its value to the URI of the PostgreSQL database.
3. Add another key named token and set its value to the token given to you from a bot account for Discord. If you do not know how to create a bot account or get
   its token, please refer to Discord's [documentation](https://discordpy.readthedocs.io/en/latest/discord.html).
