# Take5.py
# A quick text based interface for my Take 5 game module
# By Thomas Albertine


from Game.Game import Game
from Game.Game import Player
import utils
import traceback

import sys
import random
import importlib
import pathlib

import argparse
FLAG_INTERACTIVE = False

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
ais = {}
for aiModule in filter(lambda x: x.stem != "__init__", path.glob("*.py")):
    # Try to treat everything in the AIs folder as something that could 
    #   potentially be an AI module, except the __init__ of course
    # Yeah, executing strange code outside a sandbox is a massive security 
    #   hole, but it's a toy project, so I'm not going to worry about it
    tmp_module = AiModuleWrapper(aiModule)
    ais[tmp_module.getName()] = tmp_module

parser = argparse.ArgumentParser()
parser.add_argument("--interactive", help="interactively build/play one table of Take5",
                    action="store_true")      
parser.add_argument("-v", "--verbose", help="enables additional print statements", action="store_true")      
parser.add_argument("--autobattle-AI", help="chooses the AI to automatically battle against the other AIs", choices=[i for i in ais.keys() if i != "userInput"])
parser.add_argument("-n", "--autobattle-NumberOfTables", help="set the number of tables (random-unique configurations of AIs) for the autobattle", type=int, default=50)
parser.add_argument("-r", "--autobattle-Rounds", help="set the number of rounds each table will play", type=int, default=100)
parser.add_argument("-mp", "--autobattle-MaxPlayers", help="set the maximum number of players at each table", type=int, default=10)
parser.add_argument("-np", "--autobattle-MinPlayers", help="set the minimum number of players at each table", type=int, default=2)
args = parser.parse_args()

print(dir(args))
assert args.autobattle_AI in [None, *ais.keys()]

def vprint(*args, **kvargs):
    if args.verbose:
        print(*args, **kvargs)

if args.autobattle_AI is None and not args.interactive:
    # We will fix that.
    aiChoice = utils.choiceInput(list(ais.keys()), "Which AI module would you like to use for ")
    args.autobattle_AI = list(ais.keys())[aiChoice]

intMapAIs = {i:k for i,k in zip(range(len(ais)), ais.keys())}

if args.interactive:
    playerCount = utils.intInput("How many players would you like? ", 2, 10)

    game = Game(playerCount)
    players = game.getPlayers()
    for i,player in enumerate(players):
        player.setName(input("What would you like to name player " + str(i) + "? "))
        ai = None
        while ai is None:
            aiChoice = utils.choiceInput(list(ais.keys()), "Which AI module would you like to use for " + player.name + "? ") # Bypass the getter so as not to give up an easter egg just yet. Hee hee hee!
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
    number_tables = args.autobattle_NumberOfTables
    sample_size_per_table = args.autobattle_Rounds
    results = {i: [0, 0] for i in ais.keys() if i != "userInput"}
    tested_ai_results = [0,0]
    random.seed()
    for table in range(number_tables):
        number_players = random.randint(args.autobattle_MinPlayers, args.autobattle_MaxPlayers)
        print(f"Table {table+1}/{number_tables} with {number_players} players.")
        player_ai_ids = [args.autobattle_AI, *[random.randint(0, len(intMapAIs)-2) for i in range(1, number_players)]]
        gameResults = dict()
        for iteration in range(sample_size_per_table):
            game = Game(number_players)
            players = game.getPlayers()
            for i, player in enumerate(players):
                if i == 0:
                    player.setName(args.autobattle_AI)
                    ais[args.autobattle_AI].attachToPlayer(player)
                else:
                    player.setName(f"AI_{intMapAIs[player_ai_ids[i]]}_{i}")
                    ais[intMapAIs[player_ai_ids[i]]].attachToPlayer(player)
            scoreList = game.playGame()
            for name, score in scoreList:
                gameResults[name] = gameResults.get(name, 0) + score
        tested_ai_results = [tested_ai_results[0] + gameResults[args.autobattle_AI], tested_ai_results[1] + sample_size_per_table]
        best_results = {i: [0, 0] for i in ais.keys() if i != "userInput"}
        for tk in gameResults.keys():
            if tk != args.autobattle_AI:
                k = tk.split("_")[1] 
                if best_results[k][1] != 0 and best_results[k][0] > gameResults[tk]:
                    best_results[k] = [gameResults[tk], sample_size_per_table]
                elif best_results[k][1] == 0:
                    best_results[k] = [gameResults[tk], sample_size_per_table]
        for k in best_results.keys():
            results[k] = [results[k][0] + best_results[k][0], results[k][1] + best_results[k][1]]
            vprint(f"{k}: {float(best_results[k][0])/sample_size_per_table:.5f}",end='\t')
        vprint()
    print("--End testing--")
    print(f"Main AI score average: {float(tested_ai_results[0])/tested_ai_results[1]:.5f}")
    for ai_name in results.keys():
        print(f"{ai_name}:\t\tplayed {results[ai_name][1]} games, averaging {float(results[ai_name][0])/results[ai_name][1]:.5f}")
