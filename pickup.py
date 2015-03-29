import ibid
from ibid.plugins import Processor, handler, match
import random

##### TO DO #####
# Add !server to show IP but no pass
# Figure out how ibid does databases so I can maybe make use of it
# Add some admin commands like !forcemove/!forceremove/!forceadd and !swap

class Pickup(Processor):
    event_types = (u'message', u'state') # Added 'state' to be able to handle joins/quits/nick change events
    addressed = False # Doesn't requre a person to say the bots name for the command to work
    emptySlot = u'(?)'
    gameOn = False
    playerCount = 0
    maxPlayers = 10
    startDelay = 60
    lastTeams = u''
    serverIP = "154.127.61.63:27116"
    serverPass = "apples"
    teams = [[emptySlot for x in range(5)] for x in range(2)] # Two dimensional array (list?) where teams[0] is team A and teams[1] is team B

    def teams_reset(self):
        """Resets the teams in the format [u'(?)', u'(?)', u'(?)', u'(?)', u'(?)']"""
        return [[self.emptySlot for x in range(5)] for x in range(2)]


    def teams_display(self):
        """ Takes the teams list and formats it nicely for output on IRC.
        Looks like: TeamA[0/5]: (?), (?), (?), (?), (?) TeamB[0/5]: (?), (?), (?), (?), (?)"""
        team = ""
        def countPlayers(team):
            playerCount = 0
            for player in team:
                if player != "(?)":
                    playerCount += 1
            return playerCount
        playerCount = countPlayers(self.teams[0])
        team = u'TeamA[%d/%d]: ' % (playerCount, len(self.teams[0]))
        team += u', '.join(self.teams[0])
        playerCount = countPlayers(self.teams[1])
        team += u' TeamB[%d/%d]: ' % (playerCount, len(self.teams[1]))
        team += u', '.join(self.teams[1])
        return team

    def startGame(self, event):
        """Starts the game once the queue is full."""
        if self.playerCount == self.maxPlayers:
            players = []
            for team in range(2):
                for player in range(len(self.teams[0])):
                    players.append(self.teams[team][player][1:-1])
            self.gameOn = False
            self.lastTeams = self.teams_display()
            event.addresponse(u'The game has started! PM\'ing all players the server details', address=False)
            for player in players:
                event.addresponse(u'Paste this into your console to connect - password %s;connect %s' % (self.serverPass, self.serverIP), target=player, address=False)
            self.playerCount = 0
            self.lastTeams = self.teams_display()
        else:
            pass # Dunno

    def playerAdd(self, nick, team):
        """Adds a player to a team. 
        team a = 0, team b = 1"""
        if self.teams[team].count(u'(?)') == 0:
            event.addresponse(u'Team full!', address=False)
            return
        else:
            for index, slot in enumerate(self.teams[team]):
                if slot == self.emptySlot:
                    self.teams[team][index] = u'(%s)' % nick
                    self.playerCount += 1
                    return
    
    def playerRemove(self, nick, team):
        """Removes a player from a team. 
        team a = 0, team b = 1"""
        if self.teams[team].count(u'(%s)' % nick) != 1:
            event.addresponse(u'Player not added', address=False)
            return
        else:
            for index, slot in enumerate(self.teams[team]):
                if slot == u'(%s)' % nick:
                    self.teams[team][index] = self.emptySlot
                    self.playerCount -= 1
                    return

    @match(r'^!(?:help|commands)$')
    def help(self, event):
        """Displays help in IRC."""
        event.addresponse(u'!sg to create a new game. !add (or !add [a|b]) to add to it. !rem to remove from the pickup. !teams to see players added.', target=event['sender']['nick'], notice=True, address=False)
        event.addresponse(u'!move to move yourself to the other team. !lastteams to see players added to the last pickup.', target=event['sender']['nick'], notice=True, address=False)

    @match(r'^!info$')
    def info(self, event):
        """Just displays some info. Not really needed but people kept using the command."""
        event.addresponse(u'GameBot based on Ibid. Pickup plugin by Russ. Type !help for more commands.', target=event['sender']['nick'], notice=True, address=False)
        
    @match(r'^!lastteams$')
    def lastteams(self, event):
        if self.lastTeams == u'':
            event.addresponse(u'No last teams on record, perhaps bot reset?', address=False)
        else:
            event.addresponse(self.lastTeams, address=False)

    @match(r'^!(?:sg|start)$')
    def game_start(self, event):
        """Starts a new pickup and displays the teams in IRC."""
        if not self.gameOn:
            self.playerCount = 0
            self.gameOn = True
            self.teams = self.teams_reset()
            event.addresponse(u'Game Started!', address=False)
            event.addresponse(self.teams_display(), address=False)
        else:
            event.addresponse(u'Game already started!', address=False)

    @match(r'^!(?:cg|cancel)$')
    def game_cancel(self, event):
        """Cancels the pickup if one is active."""
        if self.gameOn:
            self.gameOn = False
            event.addresponse(u'Game Cancelled.', address=False)
        else:
            event.addresponse(u'No game to cancel.', address=False)

    @match(r'^!(?:status|teams|players)$')
    def game_status(self, event):
        """Displays the teams along with how many slots are open."""
        if self.gameOn:
            event.addresponse(self.teams_display(), address=False)
            openSlots = len(self.teams[0] + self.teams[1]) - self.playerCount
            event.addresponse(u'Open slots: %d' % openSlots, address=False)
        else:
            event.addresponse(u'There is no game in progress.', address=False)

    @match(r'^!add\s?(\w?)$')
    def game_add(self, event, team=None):
        "Adds a player to a team or picks one at random if the team isn't specified."""
        if self.gameOn:
            if u'(%s)' % event['sender']['nick'] not in self.teams[0] and u'(%s)' % event['sender']['nick'] not in self.teams[1]: # CHecks if the person isn't already added
                if team == "":
                    if self.teams[0].count(u'(?)') == 0: # Checks if team A is full, adds to B if it is
                        self.playerAdd(event['sender']['nick'], 1)
                        event.addresponse(self.teams_display(), address=False)
                    elif self.teams[1].count(u'(?)') == 0: # Checks if team B is full, adds to A if it is
                        self.playerAdd(event['sender']['nick'], 0)
                        event.addresponse(self.teams_display(), address=False)
                    else: # If neither team A nor team B are full then it picks one at random
                        self.playerAdd(event['sender']['nick'], random.randint(0,1))
                        event.addresponse(self.teams_display(), address=False)
                elif team.lower() == "a":
                    self.playerAdd(event['sender']['nick'], 0)
                    event.addresponse(self.teams_display(), address=False)
                elif team.lower() == "b":
                    self.playerAdd(event['sender']['nick'], 1)
                    event.addresponse(self.teams_display(), address=False)
                else:
                    event.addresponse(u'Invalid team selected', address=False)
            else:
                event.addresponse(u'You\'re already added!', address=False)
        else:
            event.addresponse(u'There is no game to add to.', address=False)

        if self.playerCount == self.maxPlayers: # Checks if the game is full and triggers a timer to start the game
            event.addresponse(u'Game is full! You have %d seconds to make changes before the game starts.' % self.startDelay, address=False)
            ibid.dispatcher.call_later(self.startDelay, self.startGame, event)

    @match(r'^!(?:rem|rm|remove|removeme|quit|leave)$')
    def game_remove(self, event):
        """Removes a player from the game."""
        if self.gameOn:
            if u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]: # Checks if the player is even added
                if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If person is in team A
                    self.playerRemove(event['sender']['nick'], 0)
                    event.addresponse(self.teams_display(), address=False)
                if u'(%s)' % event['sender']['nick'] in self.teams[1]: # If person is in team B
                    self.playerRemove(event['sender']['nick'], 1)
                    event.addresponse(self.teams_display(), address=False)
            else:
                event.addresponse(u'You\'re not added to the pickup', address=False)
        else:
            event.addresponse(u'No game to remove from.', address=False)

    @match(r'^!(?:move|moveme)$')
    def playerMove(self, event):
        """Moves a player to the opposite team."""
        if self.gameOn:
            if self.teams[0].count(u'(?)') >= 1: # This just checks if both teams have space or not
                teamASpace = True
            if self.teams[0].count(u'(?)') >= 1:
                teamBSpace = True
            if u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person is added
                if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If the person is in team A
                    if teamBSpace:
                        self.playerRemove(event['sender']['nick'], 0)
                        self.playerAdd(event['sender']['nick'], 1)
                        event.addresponse(self.teams_display(), address=False)
                elif u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person is in team B
                    if teamASpace:
                        self.playerRemove(event['sender']['nick'], 1)
                        self.playerAdd(event['sender']['nick'], 0)
                        event.addresponse(self.teams_display(), address=False)
            else:
                event.addresponse(u'You\'re not added to the game.', address=False)
        else:
            event.addresponse(u'No game in progress.', address=False)
            

    # So because we're not capturing text from the chat for this, we must make
    # use of @handler instead of @match which will let us get access to other
    # events. At the top we added 'state' to event_types to make this possible.
    # Every event has a type, nick change/join/quit are all of type 'state.'
    # From what I can tell the event's 'state' is either online or offline.
    # Leaving the channel will trigger an 'offline' state,
    # Joining the channel will trigger an 'online' state,
    # Changing nicks will trigger both an 'online' AND 'offline' state
    # In the case of a nick change, the event will also contain an element 'othername'
    # For nick change tracking we discard the offline event and make use of 'othername'
    # from the online event to change the persons nick in the pickup if added.
    @handler
    def nickTracker(self, event):
        """Tracks nicks joining, leaving or changing."""
        if event.type == u'state': # There may be other events happening, we don't care about them.
            if event.state == u'online': # This catches people joining the channel or nick change
                if hasattr(event, 'othername'): # This checks if the event is from a nick change
                    if u'(%s)' % event['othername'] in self.teams[0] or u'(%s)' % event['othername'] in self.teams[1]:
                        if u'(%s)' % event['othername'] in self.teams[0]:
                            self.playerRemove(event['othername'], 0)
                            self.playerAdd(event['sender']['nick'], 0)
                        elif u'(%s)' % event['othername'] in self.teams[1]:
                            self.playerRemove(event['othername'], 1)
                            self.playerAdd(event['sender']['nick'], 1)
                else: # If the event wasn't from a nick change then it's because someone joined the channel
                    if self.gameOn: # If a game is on we want to notify the player about it
                        openSlots = len(self.teams[0] + self.teams[1]) - self.playerCount
                        event.addresponse(u'Pickup in progress, %d slots open, !add to join.' % openSlots, target=event['sender']['nick'], notice=True, address=False)
                        event.addresponse(self.teams_display(), target=event['sender']['nick'], notice=True, address=False)
            elif event.state == u'offline': # This catches people leaving the channel or nick change
                if hasattr(event, 'othername'): # If a nick changed, ignore this crap
                    pass
                elif u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the nick that left is added to the pickup
                    if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If the person was added to team A
                        self.playerRemove(event['sender']['nick'], 0)
                        event.addresponse(self.teams_display(), address=False)
                    elif u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person was added to team B
                        self.playerRemove(event['sender']['nick'])
                        event.addresponse(self.teams_display(), address=False)
