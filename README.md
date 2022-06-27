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


[Add the bot to your server](https://discord.com/oauth2/authorize?client_id=807859649621524490&permissions=33792&scope=applications.commands%20bot)  
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

#### /help `query`
- Dumps explanations in chat

`query`: a choice of what to ask about. QUICKSTART will be a new user's first aide.

##### /headpat `qty`
- receive random headpat images
- headpat images are added directly to the bot files. To request one be added, contact the author

`qty`: specifies how many pats to receive. Between 1 and 4 inclusive

##### /options `option value`
Change your server options for polls

`option`: selects which option to edit
- PollWaifuCount: How Many Waifus to include in each poll.
- PollParticipationCheckStartHours: Minimum length of time for a poll to run before starting auto-close checks. Unused
- PollParticipationCheckDeltaHours: How often to perform an auto-close check after starting. Unused
- PollEndHours: How long to wait since a poll has started before forcibly closing it. Unused
- PollParticipationCheckCount: Number of people who must have confirmed their vote when an auto-close check runs to close the poll. Unused
- PollWaifuImageSizePixels: How large to make each waifu image in a poll. Unimplemented
- PollStartNextGapHours: How long to wait after a poll has ended to start the next one. Unused

`value`: value to set the selected option to

### /waifu
Command Family for waifu polls

`waifu` supports autocomplete. It represents a waifu as stored in minimal folder structure. that is: `source material`/`waifu name`

##### /waifu suggest `image name source`
Suggest a waifu for inclusion in the main waifu database, or a new image for an existing one.

`image`: a discord attachment for the image to be used

`name`: name of waifu to suggest. supports autocomplete. typing a source in this field will show existing waifus from that source

`source`: source material of waifu to suggest, preffering series. supports autocomplete. typing a waifu name in this field will suggest known sources with that waifu

##### /waifu show `waifu`
Shows an image of a waifu in the database. If the waifu has multiple images, which one to use is selected randomly.

##### /waifu getList `scope`
get a list of all waifus available as a txt file

`scope`: how large to search
- Local: Server Only, includes the ratings of the waifus from polls
- Global: All Waifus.
- NotInServer: A list of all waifus in the global set that are not in the server. Essentially `Global` minus `Local`.

### /gacha
Family of gacha-game related commands

##### /gacha roll `spend`
Roll a random unclaimed waifu from the server polls to collect

`spend` : number of tickets to spend. More tickets tends to get higher rated waifus

##### /gacha collection
See which waifus you've rolled

### /tickets
Economy-based tickets

##### /tickets get
See how many tickets you have

### /poll
Family of poll-related commands

##### /poll start
Begins a waifu poll. Posts an image collage of selected waifus, and creates buttons for approval-based voting.

##### /poll end
Manually end the most recent poll and calculate results

##### /poll result `pollNum`
Show the results graphs from any poll run after 4.2.0

`pollNum` : index of the poll to get, where 0 is the first poll in the server. Defaults to the most recent poll.

### /manageWaifus
command family for managing server waifus. seperate command group to support command permissioning

`waifu` supports autocomplete. It represents a waifu as stored in minimal folder structure. that is: `source material`/`waifu name`

##### /manageWaifus pull `waifu`
Add a waifu from the master database to your server's waifupolls. Newly added waifus are always initialized with a rating of 1

##### /manageWaifus remove `waifu`
remove a waifu from your server

##### /manageWaifus pullCSV `csv`
Pull multiple waifus simulatenously using a csv file

`csv`: A comma-seperated-values file, where each line contains a (`name`,`source`) pair in the first two columns. Data in other columns will be ignored.

## Todo
See Todo.md, but high level:

Gacha Game
More Options
More Responses

Contributions welcome, feel free to make pull requests.


## License
Licensed under the GPLv3.0 license. See LICENSE file.

## Credits
LordOfEnnui#8710: V0 reddit bot, V1 Implementation and methodology consultation.  
Sayeth_We#0663: V1 Implementation, Equation Design, V2 Rewrite

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
Assuming The Environment Variables are set up, running `headpatbot.py` will start the bot and connect to discord automatically.
