# Fixes the type hinting for 'list[int]'.
from __future__ import annotations
from typing import TypedDict

# DemocracyBot.py
# An AI module that instantiates all the other AI modules, and lets them vote on which card to play
# By Thomas Albertine
import copy
import Game.Game
import pathlib
import random
from AIModuleWrapper import AiModuleWrapper

AI_BLACKLIST = {"userInput", "DemocracyBot"}

# Setup()
#   Used to initialize an AI state required later. Optional.
# Takes arguments:
#   Number of players
# Returns optionally an object containing the AI's state
def Setup(playerCount: int):
    path = pathlib.Path("AIs")
    ais = {}
    for aiModule in filter(lambda x: x.stem != "__init__", path.glob("*.py")):
        # Try to treat everything in the AIs folder as something that could 
        #   potentially be an AI module, except the __init__ of course
        # Yeah, executing strange code outside a sandbox is a massive security 
        #   hole, but it's a toy project, so I'm not going to worry about it
        tmp_module = AiModuleWrapper(aiModule)
        ais[tmp_module.getName()] = tmp_module
        tmp_module.load()

    for aiName in AI_BLACKLIST:
        if aiName in ais:
            del ais[aiName]
    return StateOfDemocracy(ais, playerCount)

# PostGame()
#   Used to present results, or to use results to train machine learning models, etc. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

def PostGame(ai: StateOfDemocracy, scores: list[tuple[string, int]]):
    ai.PostGame(scores)

# PostRound()
#   Used notify that a round is over, and that the cards will be reshuffled and dealt out again. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

def PostRound(ai: StateOfDemocracy, scores: list[tuple[string, int]]):
    ai.PostRound(scores)
            
# PostTurn()
#   Used notify that a turn is over, and which cards everyone has played. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players cards in player order starting with the current player
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

def PostTurn(ai: StateOfDemocracy, playedCards: list[int], scores: list[tuple[string, int]]):
    ai.PostTurn(playedCards, scores)

# PlayCard()
#   Determines which card from the player's hand they should play
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of cards in the player's hand, sorted in ascending order
#   A list of lists representing the current state of the card rows
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
# Returns a card in the player's hand that they intend to play
def PlayCard(ai: StateOfDemocracy, hand : list[int], rows: list[list[int]], scores: list[tuple[string, int]]):
    return ai.PlayCard(hand, rows, scores)


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
def ChooseRow(ai: StateOfDemocracy, card: int, hand: list[int], rows: list[list[int]], cardsPlayed: list[int], scores: list[tuple[string, int]]):
    return ai.ChooseRow(card, hand, rows, cardsPlayed, scores)

####################

class StateOfDemocracy:
    def __init__(self, citizens : dict, playerCount : int):
        self.citizens = citizens
        self.aiState = {}
        for name, ai in self.citizens.items():
            if "Setup" in dir(ai.module):
                self.aiState[name] = ai.module.Setup(playerCount)
            else:
                self.aiState[name] = None

    def PostGame(self, scores: list[tuple[string, int]]):
        for name, ai in self.citizens.items():
            if "PostGame" in dir(ai.module):
                ai.module.PostGame(self.aiState[name], copy.deepcopy(scores))

    def PostRound(self, scores: list[tuple[string, int]]):
        for name, ai in self.citizens.items():
            if "PostRound" in dir(ai.module):
                ai.module.PostRound(self.aiState[name], copy.deepcopy(scores))

    def PostTurn(self, playedCards: list[int], scores: list[tuple[string, int]]):
        for name, ai in self.citizens.items():
            if "PostTurn" in dir(ai.module):
                ai.module.PostTurn(self.aiState[name], copy.copy(playedCards), copy.deepcopy(scores))

    def PlayCard(self, hand: list[int], rows: list[list[int]], scores: list[tuple[string, int]]):
        votes = dict()
        for name, ai in self.citizens.items():
            vote = ai.module.PlayCard(self.aiState[name], copy.copy(hand), copy.deepcopy(rows), copy.deepcopy(scores))
            if vote in hand:
                # Ignore votes for invalid moves
                if vote in votes:
                    # Increment the tally of votes for this card
                    votes[vote] += 1
                else:
                    # If nobody's voted for this one yet, initialize it for one vote
                    votes[vote] = 1
        winners = set()
        winningTally = -1
        for card, tally in votes.items():
            if tally == winningTally:
                winners.add(card)
            if tally > winningTally:
                winningTally = tally
                winners.clear()
                winners.add(card)
        if len(winners) == 0:
            # Nobody voted for a valid option
            return random.choice(hand)
        return random.choice(list(winners))

    def ChooseRow(self, card: int, hand: list[int], rows: list[list[int]], cardsPlayed: list[int], scores: list[tuple[string, int]]):
        votes = dict()
        for name, ai in self.citizens.items():
            vote = ai.module.ChooseRow(self.aiState[name], card, copy.copy(hand), copy.deepcopy(rows), copy.deepcopy(cardsPlayed), copy.deepcopy(scores))
            if vote in range(0, 4):
                # Ignore votes for invalid moves
                if vote in votes:
                    # Increment the tally of votes for this card
                    votes[vote] += 1
                else:
                    # If nobody's voted for this one yet, initialize it for one vote
                    votes[vote] = 1
        winners = set()
        winningTally = -1
        for card, tally in votes.items():
            if tally == winningTally:
                winners.add(card)
            if tally > winningTally:
                winners.clear()
                winners.add(card)
        if len(winners) == 0:
            # Nobody voted for a valid option
            return random.choice(hand)
        return random.choice(list(winners))