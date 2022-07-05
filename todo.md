# Todo
**Release Critical**  
_Future Feature_  
~~cancelled~~

- [x] Write README.md
- [x] Add more Waifus
- [ ] Add More Headpats
- [ ] **Test Bot**
    - Will always need more testing
    - Commands
        - [ ] headpat
        - [ ] options
        - [ ] waifu
            - [ ] suggest
            - [ ] show
            - [ ] getlist
            - [ ] pull
            - [ ] remove
            - [ ] pullCSV
            - [ ] poll
                - [ ] start
                - [ ] end

## Caching

- [x] Schedule events
- [x] Allow pushing to Postgre or other SQL
- [x] **Load Waifus from SQL**
- [x] **Load Servers from SQL**

## Options

- [x] **create server options**
- [x] **create default values**
- [x] set limits per options

## Commands

- [x] **permission checks**
- ~~[x] configurable permissions~~
    - ~~can use commands.check_any, need to find what check(s) can easily be configured user-side~~
    - permissions v2 covers this
    - [ ] set default permissions

### Help command

- [x] implement
- [x] **add documentation to commands**

### Waifus and images
- [x] **Overall database**
- [x] **pull waifus from database to server**
- [x] suggest waifus/images for database
    1. [x] send message in approval channel
    2. [x] get approval 
        - [ ] with any modifications
    3. [x] alert suggester/channel
- [x] waifus can have multiple images
- [x] **remove waifus**
- [x] List Local Waifus
- [x] List Global Waifus
- [x] **Prevent Poll from Running when not enough Waifus**
- [ ] Use Server TileSize setting
- [ ] Smarter Face detection

### Waifu Poll
- [x] **start poll**
- Automation (optional)
    - [ ] auto-start
        - time since poll ended
    - [ ] auto-end
        - Minimum time with threshold
            - Check Frequency
        - Maximum Time
- Approval voting system
    - [x] Elo System
    - [x] Selection
    - [x] Running
    - [x] collect votes
    - [x] update waifu ratings
- [ ] alert participants
- [x] fancy graphics
    - [x] Vote histogram
    - [x] Expected performance vs actual performance
    - [x] rating changes

---
## Gacha Game  
- [x] _pull from server waifus_
    - [x] spend tickets to improve your waifus somehow
- [x] _earn tickets for participating in polls_
    - [x] Earn tickets when your waifus are voted for by users other than you
- [x] waifu claim expiry
- [ ] _some kind of minigame?_

---
## Server Folder
- [x] data file
- [x] track polls
---
## Headpats
- [x] global only

## Responses
- [x] **Respond to commands**
- [x] random fetch from list
- [ ] populate response file

## Activity 
('Watching...','playing...',etc.)
- [ ] some activity text
- [ ] changing activity text