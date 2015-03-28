import ibid
from ibid.plugins import Processor, handler, match
import random

class Pickup(Processor):
    event_types = (u'message', u'state')
    addressed = False
    emptySlot = u'(?)'
    gameOn = False
    playerCount = 0
    maxPlayers = 10
    startDelay = 60
    lastTeams = ""
    serverIP = "154.127.61.63:27116"
    serverPass = "apples"
    teams = [[emptySlot for x in range(5)] for x in range(2)]

    def teams_reset(self):
        return [[self.emptySlot for x in range(5)] for x in range(2)]

    def teams_display(self, teams):
        team = ""
        def countPlayers(team):
            playerCount = 0
            for player in team:
                if player != "(?)":
                    playerCount += 1
            return playerCount
        playerCount = countPlayers(teams[0])
        team = u'TeamA[%d/%d]: ' % (playerCount, len(teams[0]))
        team += u', '.join(teams[0])
        playerCount = countPlayers(teams[1])
        team += u' TeamB[%d/%d]: ' % (playerCount, len(teams[1]))
        team += u', '.join(teams[1])
        return team

    def startGame(self, event):
        if self.playerCount == self.maxPlayers:
            players = []
            for team in range(2):
                for player in range(len(self.teams[0])):
                    players.append(self.teams[team][player][1:-1])
            self.gameOn = False
            self.lastTeams = self.teams_display(self.teams)
            event.addresponse(u'The game has started! PM\'ing all players the server details', address=False)
            for player in players:
                event.addresponse(u'Paste this into your console to connect - password %s;connect %s' % (self.serverPass, self.serverIP), target=player, address=False)
            self.playerCount = 0
        else:
            pass

    def playerAdd(self, nick, team):
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
        if self.teams[team].count(u'(%s)' % nick) != 1:
            event.addresponse(u'Player not added', address=False)
            return
        else:
            for index, slot in enumerate(self.teams[team]):
                if slot == u'(%s)' % nick:
                    self.teams[team][index] = self.emptySlot
                    self.playerCount -= 1
                    return

    @match(r'^(?:!help|!commands)$')
    def help(self, event):
        event.addresponse(u'!sg to create a new game. !add (or !add [a|b]) to add to it. !rem to remove from the pickup. !teams to see players added.', target=event['sender']['nick'], notice=True, address=False)
        event.addresponse(u'!move to move yourself to the other team.', target=event['sender']['nick'], notice=True, address=False)

    @match(r'^!info$')
    def info(self, event):
        event.addresponse(u'GameBot based on Ibid. Pickup plugin by Russ. Type !help for more commands.', target=event['sender']['nick'], notice=True, address=False)

    @match(r'^(?:!sg|!start)$')
    def game_start(self, event):
        if not self.gameOn:
            self.playerCount = 0
            self.gameOn = True
            self.teams = self.teams_reset()
            event.addresponse(u'Game Started!', address=False)
            event.addresponse(self.teams_display(self.teams), address=False)
        else:
            event.addresponse(u'Game already started!', address=False)

    @match(r'^(?:!cg|!cancel)$')
    def game_cancel(self, event):
        if self.gameOn:
            self.gameOn = False
            event.addresponse(u'Game Cancelled.', address=False)
        else:
            event.addresponse(u'No game to cancel.', address=False)

    @match(r'^(?:!status|!teams|!players)$')
    def game_status(self, event):
        if self.gameOn:
            event.addresponse(self.teams_display(self.teams), address=False)
            openSlots = len(self.teams[0] + self.teams[1]) - self.playerCount
            event.addresponse(u'Open slots: %d' % openSlots, address=False)
        else:
            event.addresponse(u'There is no game in progress.', address=False)

    @match(r'^!add\s?(\w?)$')
    def game_add(self, event, team=None):
        if self.gameOn:
            if u'(%s)' % event['sender']['nick'] not in self.teams[0] and u'(%s)' % event['sender']['nick'] not in self.teams[1]:
                if team == "":
                    if self.teams[0].count(u'(?)') == 0:
                        self.playerAdd(event['sender']['nick'], 1)
                        event.addresponse(self.teams_display(self.teams), address=False)
                    elif self.teams[1].count(u'(?)') == 0:
                        self.playerAdd(event['sender']['nick'], 0)
                        event.addresponse(self.teams_display(self.teams), address=False)
                    else:
                        self.playerAdd(event['sender']['nick'], random.randint(0,1))
                        event.addresponse(self.teams_display(self.teams), address=False)
                elif team.lower() == "a":
                    self.playerAdd(event['sender']['nick'], 0)
                    event.addresponse(self.teams_display(self.teams), address=False)
                elif team.lower() == "b":
                    self.playerAdd(event['sender']['nick'], 1)
                    event.addresponse(self.teams_display(self.teams), address=False)
                else:
                    event.addresponse(u'Invalid team selected', address=False)
            else:
                event.addresponse(u'You\'re already added!', address=False)
        else:
            event.addresponse(u'There is no game to add to.', address=False)

        if self.playerCount == self.maxPlayers:
            event.addresponse(u'Game is full! You have %d seconds to make changes before the game starts.' % self.startDelay, address=False)
            ibid.dispatcher.call_later(self.startDelay, self.startGame, event)
            
    @match(r'^(?:!rem|!rm|!remove|!removeme|!quit|!leave)$')
    def game_remove(self, event):
        if self.gameOn:
            if u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]:
                if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If person is in team A
                    self.playerRemove(event['sender']['nick'], 0)
                    event.addresponse(self.teams_display(self.teams), address=False)
                if u'(%s)' % event['sender']['nick'] in self.teams[1]: # If person is in team B
                    self.playerRemove(event['sender']['nick'], 1)
                    event.addresponse(self.teams_display(self.teams), address=False)
            else:
                event.addresponse(u'You\'re not added to the pickup', address=False)
        else:
            event.addresponse(u'No game to remove from.', address=False)
            
    @match(r'^(?:!move|!moveme)$')
    def playerMove(self, event):
        if self.gameOn:
            if self.teams[0].count(u'(?)') >= 1:
                teamASpace = True
            if self.teams[0].count(u'(?)') >= 1:
                teamBSpace = True
            if u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person is added
                if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If the person is in team A
                    if teamBSpace:
                        self.playerRemove(event['sender']['nick'], 0)
                        self.playerAdd(event['sender']['nick'], 1)
                        event.addresponse(self.teams_display(self.teams), address=False)
                elif u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person is in team B
                    if teamASpace:
                        self.playerRemove(event['sender']['nick'], 1)
                        self.playerAdd(event['sender']['nick'], 0)
                        event.addresponse(self.teams_display(self.teams), address=False)
            else:
                event.addresponse(u'You\'re not added to the game.', address=False)
        else:
            event.addresponse(u'No game in progress.', address=False)
            

    @handler
    def nickTracker(self, event):
        if event.type == u'state':
            if event.state == u'online':
                if hasattr(event, 'othername'):
                    if u'(%s)' % event['othername'] in self.teams[0] or u'(%s)' % event['othername'] in self.teams[1]:
                        for i in range(2):
                            for player in range(len(self.teams[i])):
                                if self.teams[i][player] == u'(%s)' % event['othername']:
                                    self.teams[i][player] = u'(%s)' % event['sender']['nick']
                                    break
                else:
                    if self.gameOn:
                        event.addresponse(u'Pickup in progress, !add to join.', target=event['sender']['nick'], notice=True, address=False)
                        event.addresponse(self.teams_display(self.teams), target=event['sender']['nick'], notice=True, address=False)
            elif event.state == u'offline':
                if hasattr(event, 'othername'):
                    pass
                elif u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]:
                    for i in range(2):
                        for player in range(len(self.teams[i])):
                            if self.teams[i][player] == u'(%s)' % event['sender']['nick']:
                                self.teams[i][player] = self.emptySlot
                                self.playerCount -= 1
                                event.addresponse(self.teams_display(self.teams), address=False)
                                break
