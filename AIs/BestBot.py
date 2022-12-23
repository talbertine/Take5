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

    def getCardsInRange(self, first: int, last: int):
        """Get the number of cards left in the given range (inclusive)"""
        return len([x for x in self.cards_remaining if x >= first and x <= last])

    @staticmethod
    def _getBucket(card: int):
        return round((card - 1) * (CardCounter.NUM_BUCKETS - 1) / (Game.NUM_CARDS - 1))

class RowInfo:
    """Helper class to characterize a row"""
    def __init__(self, row: list[int], counter: CardCounter):
        self.value = max(row)
        self.points = Game.getTotalPoints(row)
        self.count = len(row)
        self.slots_left = Game.ROW_SIZE - self.count
        self.max_value = Game.NUM_CARDS
        self.possible_count = counter.getCardsInRange(self.value, self.max_value)

    def setNextRow(self, other, counter: CardCounter):
        self.max_value = other.value - 1
        self.possible_count = counter.getCardsInRange(self.value, self.max_value)

class BestBotState:
    def __init__(self, playerCount: int):
        self.player_count = playerCount
        self.card_counter = CardCounter(playerCount)
        self.reset()
        
    def reset(self):
        """Reset to inital state"""
        self.round_started = False
        self.card_counter.reset()

    def prepareTurn(self, hand: list[int], rows: list[list[int]]):
        if self.round_started:
            self.cards_remaining = len(hand)
        else:
            # Start the round
            self.countCards(hand)
            for r in rows:
                self.countCards(r)
            self.cards_remaining = Game.HAND_SIZE
            self.round_started = True


    def countCards(self, cards: list[int]):
        for c in cards:
            self.card_counter.countCard(c)

    def playTurn(self, hand: list[int], rows: list[list[int]], scores: list[tuple[str, int]]):
        """PLay the turn and select the best card"""

        row_infos = sorted([RowInfo(r, self.card_counter) for r in rows], key=lambda r: r.value)

        for i in range(len(row_infos)-1):
            row = row_infos[i]
            next_row = row_infos[i + 1]
            row.setNextRow(next_row, self.card_counter)
        
        # Cards are in ascending order
        weights = [self._weighCard(c, row_infos) for c in hand]
        min_weight = min(weights)
        min_cards = []

        for i in range(len(weights)):
            if weights[i] == min_weight:
                min_cards.append(hand[i])

        if len(min_cards) > 1:
            # Multiple cards with same weight.
            # For now, choose the highest one
            # TODO: better tiebreaker here.
            # Ideas: hardest card to play, cards closest to other cards, etc
            return min_cards[-1]
        else:
            # Return only card
            return min_cards[0]


    def _weighCard(self, card: int, rows: list[RowInfo]) -> float:
        """Get the expected points for the given card. Lower is better"""

        # Find the row that this card would play to
        played_row = None
        for r in rows:
            if (card > r.value) and (card <= r.max_value):
                played_row = r

        # TODO: calculate the chance that this row is taken before
        # it resolves to our card
        if played_row is not None:
            # This card would likely resolve to this row.
            # Calculate how likely we are to get points here.
            return self._weighCardForRow(card, played_row)
        else:
            # Card would not resolve to any row.
            return self._weighCardForBreak(card, rows)

    def _weighCardForRow(self, card: int, row: RowInfo):
        """Give the expected points of playing this card to this row"""
        if row.slots_left >= self.player_count:
            # No chance of it breaking (unless there is fuckery).
            break_chance = 0.0
        else:
            # How likely is this row to break?

            # How many cards are between this row and our card?
            remaining = self.card_counter.getCardsInRange(row.value, card - 1)

            # Normalize the weight by number of remaining cards in the round
            norm = self.cards_remaining / Game.HAND_SIZE
            break_chance = remaining * norm / self.player_count
        
        return break_chance * row.points

    def _weighCardForBreak(self, card: int, rows: list[RowInfo]):
        """Give the expected points of this card for breaking (taking a row)"""
        # For now, we naively assume we will just take the min row.
        # TODO: improve this here by deciding how difficult this card
        # is to play (lower cards are harder to play)
        return min([r.points for r in rows])

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
    ai.prepareTurn(hand, rows)
    return ai.playTurn(hand, rows, scores)

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
