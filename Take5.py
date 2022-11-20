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

        # setup callback
        if "Setup" in dir(self.module):
            player.setSetupCallback(module.Setup)

        # game end callback
        if "PostGame" in dir(self.module):
            player.endGameCallback(module.PostGame)

        # PlayCard
        player.setTurnCallback(module.PlayCard)

        # ChooseRow
        player.setBreakCallback(module.ChooseRow)

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

game.playGame()

