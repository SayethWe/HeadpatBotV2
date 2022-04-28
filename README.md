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
V2.1.0 - slash command rewrite

[Add the bot to your server](https://discord.com/api/oauth2/authorize?client_id=807859649621524490&permissions=33792&scope=bot)  
[Join the support server](https://discord.gg/yhQzBYqFZb)

## Permissions
#### Tested, Required
Attach Files
View Channel(s)
#### Tested, not Required, Reccomended for safety
Send Messages
#### Not Required, may be used in future
Add Reactions

## Features/ Commands
All commands are slash commands
##### /headpat `qty`
- receive random headpat images
- headpat images are added directly to the bot files. To request one be added, contact the author

`qty`: specifies how many pats to receive. Between 1 and 4 inclusive

##### /options `option value`
Change your server options for polls

Checks if the user has server Administrator Permissions

`option`: selects which option to edit
- PollWaifuCount: How Many Waifus to include in each poll.
- PollParticipationCheckStartHours: Minimum length of time for a poll to run before starting atuo-close checks.
- PollParticipationCheckDeltaHours: How often to perform an auto-close check after starting.
- PollEndHours: How long to wait since a poll has started before forcibly closing it.
- PollParticipationCheckCount: Number of people who must have confirmed their vote when an auto-close check runs to close the poll.
- PollWaifuImageSizePixels: How large to make each waifu image in a poll. Unused
- PollStartNextGapHours: How long to wait after a poll has ended to start the next one. Unused

`value`: value to set the selected option to

### /waifu
Command Family for waifu polls

`name` and `source` support autocomplete.  
When Typing in a `name` field, typing a source will suggest waifus from that source.  
When typing in a `source` field, typing a name will suggest sources that have waifus with that name

`name`: The waifu's name

`source`: the media from where the waifu originates. Series names preferred
##### /waifu suggest `image name source`
Suggest a waifu for inclusion in the main waifu database, or a new image for an existing one.

`image`: a discord attachment for the image to be used

##### /waifu show `name source`
Shows an image of a waifu in the database. If the waifu has multiple images, which one to use is selected randomly.

##### /waifu getList `scope`
get a list of all waifus available as a txt file

Checks if the user has permission to attach files in the channel

`scope`: how large to search
- Local: Server Only, includes the ratings of the waifus from polls
- Global: All Waifus.
- NotInServer: A list of all waifus in the global set that are not in the server. Essentially `Global` minus `Local`. 

##### /waifu pull `name source`
Add a waifu from the master database to your server's waifupolls. Newly added waifus are always initialized with a rating of 1

Checks if the user can manage messages in the guild

##### /waifu remove `name source`
remove a waifu from your server

Checks if the user can manage messages in the guild

##### /waifu pullCSV `csv`
Pull multiple waifus simulatenously using a csv file

Checks if the user can manage messages in the guild

`csv`: A comma-seperated-values file, where each line contains a (`name`,`source`) pair in the first two columns. Data in other columns will be ignored.

#### /waifu poll
Family of poll-related commands

All Commands in this family check is the user is a server administrator

##### /waifu poll start `autoclose`
Begins a waifu poll. Posts an image collage of selected waifus, and creates buttons for approval-based voting.

`autoclose`:Whether to use server options to check and automatically close the poll after a mimnimum time and number of voters, or a maximum time.

##### /waifu poll end
Manually end the most recent poll and calculate results

## Todo
See Todo.md, but high level:

Gacha Game
More Options, including command permissions
More Responses

Contributions welcome, feel free to make pull requests.


## License
Licensed under the GPLv3.0 license. See LICENSE file.

## Credits
LordOfEnnui#8710: V1 Implementation and methodology consultation
Sayeth_We#0663: V1 Implementation, Equation Design, V2 Rewrite

## Self hosting

If you want your own master database of waifus, you can clone and self-host the repository
The bot is designed for use with free Heroku dynos, and should run with minimum setup
you can also run on a local machine.

However, any self-hosted bots should make themselves obvious as such.

#### Environment Variables to use:
`DISCORD_TOKEN`: The logon token for the bot account
`APPROVAL_CHANNEL`: Channel ID to get messages from the bot asking to approve suggested Waifus. Bot must have send permissions in this channel.
`SHARE_CHANNEL`: Channel ID to send messages from the bot when a new waifu is approved. Bot must have send permissions in this channel.
`DATABASE_URL`:Credentials link to a postgresql database for storing data. Theoretically optional when not using Heroku. Not using it has not been tested since implemented.

#### Launch File:
Assuming The Environment Variables are set up, running `headpatbot.py` will start the bot and connect to discord automatically.