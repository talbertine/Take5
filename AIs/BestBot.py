# BestBot.py
# An AI module that is simply the best
# By Tyler Howe
import random
from Game.Game import Game

class CardCounter:
    """Helper class for counting cards"""

    NUM_BUCKETS = int(Game.NUM_CARDS / Game.HAND_SIZE)

    def __init__(self, playerCount):
        self.player_count = playerCount
        self.reset()

    def reset(self):
        """Reset to inital state"""
        # Initialize the card-counting buckets.
        # We assume that each player will have a somewhat evenly distributed hand
        self.buckets = [self.player_count] * CardCounter.NUM_BUCKETS
        self.cards_remaining = list(range(1, Game.NUM_CARDS + 1))

    def countCard(self, card: int):
        """Count the given card"""

        try:
            self.cards_remaining.remove(card)
            bkt = CardCounter._getBucket(card)
            self.buckets[bkt] -= 1
        except ValueError:
            pass # Already counted

    @staticmethod
    def _getBucket(card: int):
        return round(card * CardCounter.NUM_BUCKETS / Game.NUM_CARDS)

class BestBotState:
    def __init__(self, playerCount: int):
        self.card_counter = CardCounter(playerCount)
        self.reset()
        
    def reset(self):
        """Reset to inital state"""
        self.round_started = False
        self.card_counter.reset()

    def checkRoundStart(self, hand: list[int], rows: list[list[int]]):
        if not self.round_started:
            # Start the round
            self.countCards(hand)
            for r in rows:
                self.countCards(r)
            self.round_started = True   

    def countCards(self, cards: list[int]):
        for c in cards:
            self.card_counter.countCard(c)

# Setup()
#   Used to initialize an AI state required later.
# Takes arguments:
#   Number of players
# Returns optionally an object containing the AI's state
def Setup(playerCount: int):
    return BestBotState(playerCount)

# PostRound()
#   Used notify that a round is over, and that the cards will be reshuffled and dealt out again. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
def PostRound(ai: BestBotState, scores: list[tuple[str, int]]):
    ai.reset()
            
# PostTurn()
#   Used notify that a turn is over, and which cards everyone has played. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players cards in player order starting with the current player
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
def PostTurn(ai: BestBotState, playedCards: list[int], scores: list[tuple[str, int]]):
    ai.countCards(playedCards)

# PlayCard()
#   Determines which card from the player's hand they should play
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of cards in the player's hand, sorted in ascending order
#   A list of lists representing the current state of the card rows
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
# Returns a card in the player's hand that they intend to play
def PlayCard(ai: BestBotState, hand: list[int], rows: list[list[int]], scores: list[tuple[str, int]]):
    ai.checkRoundStart(hand, rows)
    
    

    return max(hand)

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
def ChooseRow(ai, card: int, hand: list[int], rows: list[list[int]], cardsPlayed: list[int], scores: list[tuple[str, int]]):
    rowScores = [Game.getTotalPoints(r) for r in rows]
    minRow = rowScores.index(min(rowScores))
    return minRow
