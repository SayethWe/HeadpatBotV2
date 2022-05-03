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
- [ ] set limits per options

## Commands

- [x] **permission checks**
- [ ] configurable permissions
    - can use commands.check_any, need to find what check(s) can easily be configured user-side

### Help command

- [ ] implement
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
- [ ] fancy graphics
    - [x] Vote histogram
    - [x] Expected performance vs actual performance
    - [ ] rating changes

---
## Gacha Game  
- [ ] _pull from server waifus_
- [ ] _earn tickets for participating in polls_
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