# purelyRandom.py
# An AI module that plays entirely random cards, and a simple example of the interface
# By Thomas Albertine
import random

# Setup()
#   Used to initialize an AI state required later. Optional.
# Takes arguments:
#   Number of players
# Returns optionally an object containing the AI's state
def Setup(playerCount):
    # I don't want other people to be able to mess with our random number generator, so the random state will be our AI state
    # Besides, it makes a good example for if your AI idea does require state
    return RandomAIState()

# PostGame()
#   Used to present results, or to use results to train machine learning models, etc. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

# Not needed for a random player

# PostRound()
#   Used notify that a round is over, and that the cards will be reshuffled and dealt out again. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

# Not needed for a random player
            
# PostTurn()
#   Used notify that a turn is over, and which cards everyone has played. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players cards in player order starting with the current player
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

# Not needed for a random player

# PlayCard()
#   Determines which card from the player's hand they should play
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of cards in the player's hand, sorted in ascending order
#   A list of lists representing the current state of the card rows
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
# Returns a card in the player's hand that they intend to play
def PlayCard(ai, hand, rows, scores):
    ai.restoreState()
    retval = random.choice(hand)
    ai.saveState()
    return retval

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
def ChooseRow(ai, card, hand, rows, cardPlayed, scores):
    ai.restoreState()
    retval = random.randint(0, len(rows) - 1)
    ai.saveState()
    return retval

class RandomAIState:

    def __init__(self):
        random.seed()
        self.saveState()

    def restoreState(self):
        random.setstate(self.randomState)

    def saveState(self):
        self.randomState = random.getstate()