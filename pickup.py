import ibid
from ibid.plugins import Processor, handler, match, authorise
import random
import datetime
import valve.source.a2s

class Pickup(Processor):
    event_types = (u'message', u'state') # Added 'state' to be able to handle joins/quits/nick change events
    addressed = False # Doesn't requre a person to say the bots name for the command to work
    empty_slot = u'(?)'
    game_on = False
    player_count = 0
    max_players = 10
    start_delay = 60
    last_teams = u''
    permission = u'admin'
    servers = [("154.127.61.63", 27116), ('196.25.210.12', 27019), ('105.227.0.9', 2701), ('105.227.0.9', 27018)]
    passwords = ['apples', 'dgl4', 'dgl16', 'dgl15']
    teams = [[empty_slot for x in range(5)] for x in range(2)] # Two dimensional array (list?) where teams[0] is team A and teams[1] is team B

    def get_open_server(self):
        def check_servers(self):
            for server in self.servers:
                server = valve.source.a2s.ServerQuerier(server)
                info = server.get_info()
                if info['player_count'] < 1:
                    return (serber.host, server.port)
        active_server = check_servers()
        if active_server == None:
            return u'No empty server to use, perhaps wait for a game to finish or organise another server.'
        active_password = self.passwords[self.servers.index(active_server)]
        connect_string = u'password %s; connect %s:%d' % (active_password, active_server[0], active_server[1])
        return connect_string

    def teams_reset(self):
        """Resets the teams in the format [u'(?)', u'(?)', u'(?)', u'(?)', u'(?)']"""
        return [[self.empty_slot for x in range(5)] for x in range(2)]

    def teams_display(self):
        """ Takes the teams list and formats it nicely for output on IRC.
        Looks like: TeamA[0/5]: (?), (?), (?), (?), (?) TeamB[0/5]: (?), (?), (?), (?), (?)"""
        team = ""
        def countPlayers(team):
            player_count = 0
            for player in team:
                if player != "(?)":
                    player_count += 1
            return player_count
        player_count = countPlayers(self.teams[0])
        team = u'TeamA[%d/%d]: ' % (player_count, len(self.teams[0]))
        team += u', '.join(self.teams[0])
        player_count = countPlayers(self.teams[1])
        team += u' TeamB[%d/%d]: ' % (player_count, len(self.teams[1]))
        team += u', '.join(self.teams[1])
        return team

    def teams_neatify(self):
        """Rearranges the elements in the teams list so that all players names are shown
        first followed by the open slots: ['Russ', 'Zoid', 'Berg', '(?)', '(?)']"""
        for index, team in enumerate(self.teams):
            player_count = 0
            count = 0
            for player in team:
                if player != u'(?)':
                    self.teams[index][count] = player
                    player_count += 1
                    count += 1
            while player_count < 5:
                self.teams[index][player_count] = u'(?)'
                player_count += 1

    @match(r'^!shuffle$')
    @authorise()
    def shuffle(self, event):
        if self.game_on:
            self.teams_shuffle()
            event.addresponse(self.teams_display(), address=False)
        else:
            event.addresponse(u'No game on to shuffle', address=False)

    def teams_shuffle(self):
        """Shuffles the players"""
        count = 0
        shuffle_list = random.sample(self.teams[0]+self.teams[1], len(self.teams[0]+self.teams[1]))
        for item in shuffle_list:
            if count < 5:
                self.teams[0][count] = shuffle_list[count]
                count += 1
            elif count >= 5 and count < 10:
                self.teams[1][count - 5] = shuffle_list[count]
                count += 1
        self.teams_neatify()


    def start_game(self, event):
        """Starts the game once the queue is full."""
        if self.game_on: # Checks if the game is still on
            if self.player_count == self.max_players:
                players = []
                for team in range(2):
                    for player in range(len(self.teams[0])):
                        players.append(self.teams[team][player][1:-1])
                self.game_on = False
                self.last_teams = self.teams_display()
                event.addresponse(u'The game has started! PM\'ing all players the server details', address=False)
                server_info = self.get_open_server()
                for player in players:
                    event.addresponse(u'Paste this into your console to connect - %s' % server_info, target=player, address=False)
                self.player_count = 0
                self.last_teams = "[%s] %s" % (datetime.datetime.now().strftime('%H:%M:%S'), self.teams_display())
            else:
                pass # Dunno
        else:
            pass # ayyyy lmao

    def player_remove(self, event, nick, team):
        """Removes a player from a team.
        team a = 0, team b = 1"""
        if self.teams[team].count(u'(%s)' % nick) != 1:
            event.addresponse(u'Player not added', address=False)
            return
        else:
            for index, slot in enumerate(self.teams[team]):
                if slot == u'(%s)' % nick:
                    self.teams[team][index] = self.empty_slot
                    self.player_count -= 1
                    self.teams_neatify()
                    return

    def player_add(self, event, nick, team):
        """Adds a player to a team.
        team a = 0, team b = 1, random = nothing."""
        def add(self, nick, team):
            for index, slot in enumerate(self.teams[team]):
                if slot == self.empty_slot:
                    self.teams[team][index] = u'(%s)' % nick
                    self.player_count += 1
                    event.addresponse(self.teams_display(), address=False)
                    return
        if u'(%s)' % nick not in self.teams[0] and u'(%s)' % nick not in self.teams[1]: # Checks if the player isn't already added
            if team != "": # If a team was specified
                if team.lower() == u'a':
                    if self.teams[0].count(u'(?)') != 0:
                        add(self, nick, 0)
                    else:
                        event.addresponse(u'Team full.', address=False)
                elif team.lower() == u'b':
                    if self.teams[1].count(u'(?)') != 0:
                        add(self, nick, 1)
                    else:
                        event.addresponse(u'Team full.', address=False)
                else:
                    event.addresponse(u'Invalid team selection.', address=False) # This never triggers?
            else: # If a team wasn't specified then random
                if self.teams[0].count(u'(?)') == 0 and u'(%s)' % nick not in self.teams[1]: # If team A is full and the player isn't already in B then just add straight to B
                    add(self, nick, 1)
                elif self.teams[1].count(u'(?)') == 0 and u'(%s)' % nick not in self.teams[0]: # Same as above
                    add(self, nick, 0)
                elif u'(%s)' % nick not in self.teams[0] and u'(%s)' % nick not in self.teams[1]: # If neither A nor B are full then random between the two
                    add(self, nick, random.randint(0,1))
        else:
            event.addresponse(u'%s is already added' % nick, address=False)

    @match(r'^!(?:help|commands)$')
    def help(self, event):
        """Displays help in IRC."""
        event.addresponse(u'!sg to create a new game. !add (or !add [a|b]) to add to it. !rem to remove from the pickup. !teams to see players added.', target=event['sender']['nick'], notice=True, address=False)
        event.addresponse(u'!move to move yourself to the other team. !lastteams to see players added to the last pickup.', target=event['sender']['nick'], notice=True, address=False)

    @match(r'^!info$')
    def info(self, event):
        """Just displays some info. Not really needed but people kept using the command."""
        event.addresponse(u'GameBot based on Ibid. Pickup plugin by Russ. Type !help for more commands.', target=event['sender']['nick'], notice=True, address=False)

    @match(r'^!last(?:teams|game)$')
    def lastteams(self, event):
        if self.last_teams == u'':
            event.addresponse(u'No last teams on record, perhaps bot reset?', address=False)
        else:
            event.addresponse(self.last_teams, address=False)

    @match(r'^!(?:sg|start)$')
    def game_start(self, event):
        """Starts a new pickup and displays the teams in IRC."""
        if not self.game_on:
            self.player_count = 0
            self.game_on = True
            self.teams = self.teams_reset()
            event.addresponse(u'Game Started!', address=False)
            event.addresponse(self.teams_display(), address=False)
        else:
            event.addresponse(u'Game already started!', address=False)

    @match(r'^!(?:cg|cancel)$')
    @authorise()
    def game_cancel(self, event):
        """Cancels the pickup if one is active."""
        if self.game_on:
            self.game_on = False
            event.addresponse(u'Game Cancelled.', address=False)
        else:
            event.addresponse(u'No game to cancel.', address=False)

    @match(r'^!(?:status|teams|players)$')
    def game_status(self, event):
        """Displays the teams along with how many slots are open."""
        if self.game_on:
            event.addresponse(self.teams_display(), address=False)
            open_slots = len(self.teams[0] + self.teams[1]) - self.player_count
            event.addresponse(u'Open slots: %d' % open_slots, address=False)
        else:
            event.addresponse(u'There is no game in progress.', address=False)

    @match(r'^!add\s?(\w?)$')
    def game_add(self, event, team=None):
        if self.game_on:
            self.player_add(event, event['sender']['nick'], team)
        else:
            event.addresponse(u'No game in progress.', address=False)
        if self.player_count == self.max_players: # Checks if the game is full and triggers a timer to start the game
            event.addresponse(u'Game is full! You have %d seconds to make changes before the game starts.' % self.start_delay, address=False)
            ibid.dispatcher.call_later(self.start_delay, self.start_game, event)

    @match(r'^!(?:rem|rm|remove|removeme|quit|leave)$')
    def game_remove(self, event):
        """Removes a player from the game."""
        if self.game_on:
            if u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]: # Checks if the player is even added
                if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If person is in team A
                    self.player_remove(event, event['sender']['nick'], 0)
                    event.addresponse(self.teams_display(), address=False)
                if u'(%s)' % event['sender']['nick'] in self.teams[1]: # If person is in team B
                    self.player_remove(event, event['sender']['nick'], 1)
                    event.addresponse(self.teams_display(), address=False)
            else:
                event.addresponse(u'You\'re not added to the pickup', address=False)
        else:
            event.addresponse(u'No game to remove from.', address=False)

    @match(r'^!(?:move|moveme)$')
    def player_move(self, event):
        """Moves a player to the opposite team."""
        if self.game_on:
            if self.teams[0].count(u'(?)') >= 1: # This just checks if both teams have space or not
                teamASpace = True
            if self.teams[0].count(u'(?)') >= 1:
                teamBSpace = True
            if u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person is added
                if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If the person is in team A
                    if teamBSpace:
                        self.player_remove(event, event['sender']['nick'], 0)
                        self.player_add(event, event['sender']['nick'], u'b')
                elif u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person is in team B
                    if teamASpace:
                        self.player_remove(event, event['sender']['nick'], 1)
                        self.player_add(event, event['sender']['nick'], u'a')
            else:
                event.addresponse(u'You\'re not added to the game.', address=False)
        else:
            event.addresponse(u'No game in progress.', address=False)

    @match(r'^!forceadd\s?(\w*)\s?(\w?)$')
    @authorise()
    def admin_forceadd(self, event, player, team=None):
        if self.game_on:
            if player != "":
                self.player_add(event, player, team)
            else:
                event.addresponse(u'Specify a name to add', address=False)
        else:
            event.addresponse(u'No game to add to.', address=False)

    # @match(r'^!force(?:rem|remove)\s?(\w*)\s?(\w?)$')
    # @authorise()
    # def admin_forceremove(self, event, player):
    #     if self.game_on:
    #         pass
    #     else:
    #         event.addresponse(u'No game to remove from.', address=False)

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
    def nick_tracker(self, event):
        """Tracks nicks joining, leaving or changing."""
        if event.type == u'state': # There may be other events happening, we don't care about them.
            if event.state == u'online': # This catches people joining the channel or nick change
                if hasattr(event, 'othername'): # This checks if the event is from a nick change
                    if u'(%s)' % event['othername'] in self.teams[0] or u'(%s)' % event['othername'] in self.teams[1]:
                        if u'(%s)' % event['othername'] in self.teams[0]:
                            self.player_remove(event, event['othername'], 0)
                            self.player_add(event['sender']['nick'], u'a')
                        elif u'(%s)' % event['othername'] in self.teams[1]:
                            self.player_remove(event, event['othername'], 1)
                            self.player_add(event['sender']['nick'], u'b')
                else: # If the event wasn't from a nick change then it's because someone joined the channel
                    if self.game_on: # If a game is on we want to notify the player about it
                        open_slots = len(self.teams[0] + self.teams[1]) - self.player_count
                        event.addresponse(u'Pickup in progress, %d slots open, !add to join.' % open_slots, target=event['sender']['nick'], notice=True, address=False)
                        event.addresponse(self.teams_display(), target=event['sender']['nick'], notice=True, address=False)
            elif event.state == u'offline': # This catches people leaving the channel or nick change
                if hasattr(event, 'othername'): # If a nick changed, ignore this crap
                    pass
                elif u'(%s)' % event['sender']['nick'] in self.teams[0] or u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the nick that left is added to the pickup
                    if u'(%s)' % event['sender']['nick'] in self.teams[0]: # If the person was added to team A
                        self.player_remove(event, event['sender']['nick'], 0)
                        event.addresponse(self.teams_display(), address=False)
                    elif u'(%s)' % event['sender']['nick'] in self.teams[1]: # If the person was added to team B
                        self.player_remove(event, event['sender']['nick'], 1)
                        event.addresponse(self.teams_display(), address=False)
