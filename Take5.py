# Take5.py
# A quick text based interface for my Take 5 game module
# By Thomas Albertine


from Game.Game import Game
from Game.Game import Player
import utils
import traceback

import sys

import importlib
import pathlib

FLAG_INTERACTIVE = True

class MissingHookException(Exception):
    def __init__(self, hookName):
        super().__init__("Missing Hook \"" + hookName + "\"")

class AiModuleWrapper:
    """This class is meant to make it easier to set up your own AI module 
    without needing to fiddle with the rest of the project"""

    def __init__(self, path):
        """The path is a Pathlib object. It's not going to get loaded until we 
        decide we need to use it. I know I'm not sandboxing this and that's a 
        security problem, but I'm not going to make you load every potentially 
        malicious thing in the AIs folder like some kind of heathen."""
        self.path = path
        self.aiName = path.stem
        self.isLoaded = False

    def load(self):
        """Does the actual loading. Make sure to only do this on AI modules 
        you trust"""
        if self.isLoaded:
            importlib.reload(self.module)
        else:
            spec = importlib.util.spec_from_file_location(self.aiName, self.path)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
            self.isLoaded = True
        self.validate()

    def validate(self):
        """Verify that functions in the module are defined with the proper names. Some are optional, so we won't worry about those here"""
        if not self.isLoaded:
            self.load()

        # These are the mandatory hooks
        # look at attachToPlayer to see all of the hooks
        if not "PlayCard" in dir(self.module):
            raise MissingHookException("TurnCallback")
        if not "ChooseRow" in dir(self.module):
            raise MissingHookException("TurnCallback")

    def attachToPlayer(self, player : Player):
        """Attach the AI module hooks to the player object callbacks"""
        if not self.isLoaded:
            self.load()

        # Setup()
        #   Used to initialize an AI state required later. Optional.
        # Takes arguments:
        #   Number of players
        # Returns optionally an object containing the AI's state
        if "Setup" in dir(self.module):
            player.setSetupCallback(self.module.Setup)

        # PostGame()
        #   Used to present results, or to use results to train machine learning models, etc. Optional.
        # Takes arguments:
        #   The player AI object, or None if no such object was created
        #   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
        if "PostGame" in dir(self.module):
            player.setEndGameCallback(self.module.PostGame)

        # PostRound()
        #   Used notify that a round is over, and that the cards will be reshuffled and dealt out again. Useful if you're trying to count cards. Optional.
        # Takes arguments:
        #   The player AI object, or None if no such object was created
        #   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
        if "PostRound" in dir(self.module):
            player.setEndRoundCallback(self.module.PostRound)
            
        # PostTurn()
        #   Used notify that a turn is over, and which cards everyone has played. Useful if you're trying to count cards. Optional.
        # Takes arguments:
        #   The player AI object, or None if no such object was created
        #   A list of the players cards in player order starting with the current player
        #   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
        if "PostTurn" in dir(self.module):
            player.setEndTurnCallback(self.module.PostTurn)

        # PlayCard()
        #   Determines which card from the player's hand they should play
        # Takes arguments:
        #   The player AI object, or None if no such object was created
        #   A list of cards in the player's hand, sorted in ascending order
        #   A list of lists representing the current state of the card rows
        #   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
        # Returns a card in the player's hand that they intend to play
        player.setTurnCallback(self.module.PlayCard)

        # ChooseRow()
        #   If the player plays a card lower than the lowest of the cards on row ends, this function is called to choose which row
        # Takes arguments:
        #   The player AI object, or None if no such object was created
        #   The card the player played, which required them to claim a row
        #   A list of cards in the player's hand, sorted in ascending order
        #   A list of lists representing the current state of the card rows
        #   A list of all of the card played this turn
        #   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
        # Returns the index of the row the player has chosen
        player.setBreakCallback(self.module.ChooseRow)

    def getName(self):
        return self.aiName

import AIs
path = pathlib.Path("AIs")
ais = []
for aiModule in filter(lambda x: x.stem != "__init__", path.glob("*.py")):
    # Try to treat everything in the AIs folder as something that could 
    #   potentially be an AI module, except the __init__ of course
    # Yeah, executing strange code outside a sandbox is a massive security 
    #   hole, but it's a toy project, so I'm not going to worry about it
    ais.append(AiModuleWrapper(aiModule))


if FLAG_INTERACTIVE:
    playerCount = utils.intInput("How many players would you like? ", 2, 10)

    game = Game(playerCount)
    players = game.getPlayers()
    for i,player in enumerate(players):
        player.setName(input("What would you like to name player " + str(i) + "? "))
        ai = None
        while ai is None:
            aiChoice = utils.choiceInput(list(map(lambda x: x.getName(), ais)), "Which AI module would you like to use for " + player.name + "? ") # Bypass the getter so as not to give up an easter egg just yet. Hee hee hee!
            try: 
                ai = ais[aiChoice]
                ai.attachToPlayer(player)
            except Exception as e:
                player.resetCallbacks()
                print("Sorry, that AI module failed to initialize")
                traceback.print_exc(file=sys.stdout)
                print()
                ai = None

    scoreList = game.playGame()
    scoreList.sort(key=lambda x: x[1])
    print("\nFinal Ranking: ")
    for i, score in enumerate(scoreList):
        print(str(i + 1) + "\t" + str(score[1]) + "\t" + score[0])
else:
    # If you want to do a statistically relevant number of tests, you can stick that code here
    sample_size = 100
    results = dict()
    for playerCount in range(2, 10 + 1):
        print("Testing " + str(playerCount) + " Players")
        gameResults = dict()
        for iteration in range(sample_size):
            game = Game(playerCount)
            players = game.getPlayers()
            for i, player in enumerate(players):
                if i == 0:
                    player.setName("ThomasBot")
                    ais[1].attachToPlayer(player)
                else:
                    player.setName("Random" + str(i))
                    ais[0].attachToPlayer(player)
            scoreList = game.playGame()
            for result in scoreList:
                if (not result[0] in gameResults):
                    gameResults[result[0]] = 0
                gameResults[result[0]] += result[1]
        for key in gameResults.keys():
            gameResults[key] /= sample_size
        results[playerCount] = gameResults
    for playerCount, result in results.items():
        print("Players: " + str(playerCount))
        for name, aveScore in result.items():
            print(name + ": " + str(aveScore))

