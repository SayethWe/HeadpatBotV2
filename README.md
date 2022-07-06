<!--
 Copyright (C) 2022 Sayeth_We
 
 This file is part of HeadpatBot.
 
 HeadpatBot is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 HeadpatBot is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with HeadpatBot.  If not, see <http://www.gnu.org/licenses/>.
-->

# Headpatbot

A discord bot for headpats and rating waifus  
1.x.x - old discord.py implementation  
2.x.x - slash commands  
3.x.x - Directory Refactoring  
4.x.x - Permissioning  
5.x.x - Gacha game and Tickets


[Add the bot to your server](https://discord.com/api/oauth2/authorize?client_id=989370465342590977&permissions=50176&scope=bot%20applications.commands)  
[Join the support server](https://discord.gg/yhQzBYqFZb)  
[View the Source](https://github.com/SayethWe/HeadpatBotV2)

## Permissions
#### Tested, Required
Attach Files
View Channel(s)
Application Commands (Create Slash Commands in Server)
#### Tested, not Required, Reccomended for safety with possible future features
Send Messages
#### Not Required, may be used in future
Add Reactions

## Features/ Commands
All commands are slash commands
`/help QUICKSTART` will be a new user's first best aide.  

##### /headpat `qty`
### /waifu
Command Family for waifus

`waifu` fields support autocomplete. Represents a waifu as stored in minimal folder structure. that is: `source material`/`waifu name`

##### /waifu suggest `image name source`
Suggest a waifu for inclusion in the main waifu database, or a new image for an existing one.

`image`: a discord attachment for the image to be used

`name`: name of waifu to suggest. supports autocomplete. typing a source in this field will show existing waifus from that source

`source`: source material of waifu to suggest, preffering series. supports autocomplete. typing a waifu name in this field will suggest known sources with that waifu

##### /waifu show `waifu`
Shows an image of a waifu in the database. If the waifu has multiple images, which one to use is selected randomly.

##### /waifu get_list `scope`
get a list of all waifus available as a txt file

`scope`: how large to search
- Local: Server Only, includes the ratings of the waifus from polls
- Global: All Waifus.
- NotInServer: A list of all waifus in the global set that are not in the server. Essentially `Global` minus `Local`.

### /gacha
Family of gacha-game related commands

##### /gacha roll `spend`
Roll a random unclaimed waifu from the server polls to collect. Claimed waifus will eventually release back into the available pool

`spend` : number of tickets to spend. More tickets tends to get higher rated waifus

##### /gacha collection
See which waifus you've rolled

##### /gacha improve `waifu`
Spend tickets to increase the level of a waifu, lengthening the amount of time before it becomes unclaimed, as well as improving ticket income from poll votes

##### /gacha remove `waifu`
Immediately sends a waifu back to the available pool, and refunds some of the tickets spent, amount based on level and time remaining. 

##### /tickets get
See how many tickets you have to spend on rolls

### /poll
Family of poll-related commands

##### /poll start
Begins a waifu poll. Posts an image collage of selected waifus, and creates buttons for approval-based voting.

##### /poll end
Manually end the most recent poll and calculate results

##### /poll result `poll_num`
Show the results graphs from any poll run after 4.2.0

`pollNum` : index of the poll to get, where 0 is the first poll in the server. Defaults to the most recent poll.

### /manage_waifus
command family for managing server waifus. seperate command group to support command permissioning

`waifu` fields support autocomplete. Represents a waifu as stored in minimal folder structure. that is: `source material`/`waifu name`

##### /manage_waifus pull `waifu`
Add a waifu from the master database to your server's waifupolls. Newly added waifus are always initialized with a rating of 1

##### /manage_waifus remove `waifu`
remove a waifu from your server

##### /manage_waifus pull_csv `csv`
Pull multiple waifus simulatenously using a csv file

`csv`: A comma-seperated-values file, where each line contains a (`name`,`source`) pair in the first two columns. Data in other columns will be ignored.

### /options `option set_value`
get or set a server-side option.

`option`: a selection of the desired option

`set value`: optional integer to set the option to. if not included, command will echo the current value.

## Todo
See Todo.md, but high level:

More Responses
Minigame of some sort

Contributions welcome, feel free to make pull requests.


## License
Licensed under the GPLv3.0 license. See LICENSE file.

## Credits
LordOfEnnui#8710: V0 reddit bot, Implementation and methodology consultation.   
Sayeth_We#0663: V1 Implementation, Equation Design, V2 Rewrite, Ongoing Development.

### Rubber ducks:
- PineappleHugs#0001
- LordOfEnnui#8710

## Self hosting

If you want your own master database of waifus, you can clone and self-host the repository
The bot is designed for use with free Heroku dynos, and should run with minimum setup
you can also run on a local machine.

However, any self-hosted bots should make themselves obvious as such.

#### Environment Variables to use:
`DISCORD_TOKEN`: The logon token for the bot account  
`APPROVAL_CHANNEL`: Channel ID to get messages from the bot asking to approve suggested Waifus. Bot must have send message and attach file permissions in this channel.  
`ANNOUNCE_HOOK`: Webhook to send messages from the bot when a new waifu is approved.  
`DATABASE_URL`:Credentials link to a postgresql database for storing data.  
`LOGS_HOOK`: A discord webhook to send Critical, Error, and Warning logs to. Optional.  

`TEST_ENV`: Guild ID(s) to test slash commands in. Optional. Do not use in deployed environment.

#### Launch File:
Assuming The Environment Variables are set up, running `runBot.py` will start the bot and connect to discord automatically. Working directory should be the master directory. Alternately, run `heroku local` from the command line in the main directory
