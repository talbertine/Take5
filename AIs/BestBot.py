# BestBot.py
# An AI module that is simply the best
# By Tyler Howe
import copy
from Game.Game import Game
import numpy
from enum import Enum

class CardCounter:
    """Helper class for counting cards"""

    NUM_BUCKETS = int(Game.NUM_CARDS / Game.HAND_SIZE)

    def __init__(self, playerCount):
        self.player_count = playerCount
        self.reset()

    def reset(self) -> None:
        """Reset to inital state"""
        self.cards_remaining = list(range(1, Game.NUM_CARDS + 1))

    def countCard(self, card: int) -> None:
        """Count the given card"""

        try:
            self.cards_remaining.remove(card)
        except ValueError:
            pass # Already counted

    def getCardsInRange(self, first: int, last: int) -> list[int]:
        """Get the number of cards left in the given range (inclusive)"""
        return [x for x in self.cards_remaining if x >= first and x <= last]

    def getNumberOfCardsRemaining(self) -> int:
        return len(self.cards_remaining)
        
class RowInfo:
    """Helper class to characterize a row"""
    def __init__(self, *args):
        """Create a new rowinfo object with either no args or a list of cards and a card_counter"""
        arg_len = len(args)
        assert arg_len == 0 or arg_len == 2, "Invalid arg length for rowinfo"

        if len(args) > 0:
            row = args[0]
            counter = args[1]

            self.value = max(row)
            self.points = Game.getTotalPoints(row)
            self.count = len(row)
            self.slots_left = Game.ROW_SIZE - self.count
            self.max_value = Game.NUM_CARDS
            self.possible_cards = counter.getCardsInRange(self.value, self.max_value)
        else:
            self.value = 0
            self.points = 0
            self.count = 0
            self.slots_left = 0
            self.max_value = 0
            self.possible_cards = []

    def __copy__(self):
        ret = RowInfo()
        ret.value = self.value
        ret.points = self.points
        ret.count = self.count
        ret.slots_left = self.slots_left
        ret.max_value = self.max_value
        ret.possible_cards = self.possible_cards

    def linkToRow(self, other, counter: CardCounter):
        self.max_value = other.value - 1
        self.possible_cards = counter.getCardsInRange(self.value, self.max_value)

    def resolveCard(self, card: int, force_break: bool) -> int:
        """Resolve the given card to this row. Returns amount of points taken"""
        self.value = card
        card_pts = Game.cardToPoints(card)
        
        if self.slots_left == 0 or force_break:
            # Broken
            pts_taken = self.points
            self.points = card_pts
            self.count = 1
            self.slots_left = Game.ROW_SIZE - self.count
            return pts_taken
        else:
            # Not broken
            self.points += card_pts
            self.count += 1
            self.slots_left -= 1
            return 0

    @staticmethod 
    def UpdateRows(row_infos, card_counter: CardCounter):
        sorted_rows = sorted(row_infos, key=lambda r: r.value)

        for i in range(len(sorted_rows)-1):
            row = sorted_rows[i]
            next_row = sorted_rows[i + 1]
            row.linkToRow(next_row, card_counter)

        sorted_rows[-1].max_value = Game.NUM_CARDS

    @staticmethod
    def CreateFromRowList(rows: list[list[int]], card_counter: CardCounter):        
        row_infos = [RowInfo(r, card_counter) for r in rows]

        RowInfo.UpdateRows(row_infos, card_counter)

        return row_infos

def ResolveRow(card: int, rows: list[RowInfo]) -> RowInfo:
    """Find the row this card would resolve to. Returns None if it is too low"""

    played_row = None
    for r in rows:
        if (card > r.value) and (card <= r.max_value):
            played_row = r

    return played_row

class Strategy(Enum):
    SAFE = 1
    NORMAL = 2
    AGGRESSIVE = 3

class BestBotState:
    def __init__(self, playerCount: int):
        self.player_count = playerCount
        self.card_counter = CardCounter(playerCount)
        self.reset()
        
    def reset(self):
        """Reset to inital state"""
        self.turns_left = 0 # start at zero
        self.card_counter.reset()
        self.min_score = 0
        self.max_score = 0
        self.our_score = 0
        self.strategy = Strategy.NORMAL

    def prepareTurn(self, hand: list[int], rows: list[list[int]]):
        if self.turns_left == 0:
            # Start the round
            self.countCards(hand)
            for r in rows:
                self.countCards(r)

        self.turns_left = len(hand)

        # Decide how safe or aggressive we can play
        if (self.our_score > Game.TARGET_SCORE - 10):
            self.strategy = Strategy.SAFE
        elif (self.our_score == self.min_score) and (self.our_score < 20):
            self.strategy = Strategy.AGGRESSIVE
        else:
            self.strategy = Strategy.NORMAL


    def countCards(self, cards: list[int]):
        for c in cards:
            self.card_counter.countCard(c)

    def playTurn(self, hand: list[int], rows: list[list[int]], scores: list[tuple[str, int]]):
        """PLay the turn and select the best card"""

        row_infos = RowInfo.CreateFromRowList(rows, self.card_counter)

        # Cards are in ascending order
        weights = [self._weighCard(c, row_infos) for c in hand]

        # Choose a safe weight, but not too safe, if possible
        safe_weights = [x for x in weights if x < 0.5 and x > 0]

        if (len(safe_weights) > 0) and (self.strategy != Strategy.SAFE):
            min_weight = max(safe_weights)
        else:
            min_weight = min(weights)

        min_cards = []

        for i in range(len(weights)):
            if weights[i] == min_weight:
                min_cards.append(hand[i])

        if len(min_cards) > 1:
            # Multiple cards with same weight.
            # For now, choose the lowest one, since those are harder to play
            # TODO: better tiebreaker here.
            # Ideas: hardest card to play, cards closest to other cards, etc
            return min_cards[0]
        else:
            # Return only card
            return min_cards[0]


    def _weighCard(self, card: int, rows: list[RowInfo]) -> float:
        """Get the expected points for the given card. Lower is better"""

        # Find the row that this card would play to
        played_row = ResolveRow(card, rows)

        # TODO: calculate the chance that this row is taken before
        # it resolves to our card
        if played_row is not None:
            # This card would likely resolve to this row.
            # Calculate the expected points
            return self._weighCardForRow(card, played_row)
        else:
            # Card would not resolve to any row.
            return self._weighCardForBreak(card, rows)

    def _weighCardForRow(self, card: int, row: RowInfo):
        """Give the expected points of playing this card to this row"""
        
        # How many cards are between this row and our card?
        possible_cards = self.card_counter.getCardsInRange(row.value, card)
        
        # This is an attempt to estimate how likely a player would play
        # one of the remaining cards.
        total_cards_remaining = self.card_counter.getNumberOfCardsRemaining()

        if row.slots_left >= self.player_count:
            # No chance of it breaking if things go smoothly.
            # As long as we are close to this card, we should be okay
            return 0.0
        else:

            if len(possible_cards) < row.slots_left or len(possible_cards) == 0:
                # Short-circuit - no possible cards!
                return 0.0

            # How many points would this row be worth?
            avg_possible_pts = Game.getTotalPoints(possible_cards) / len(possible_cards)
            est_pts_left = avg_possible_pts * row.slots_left


            # TODO: this is assuming all players are playing randomly...
            # Probably not correct. Need to take into account other rows, etc.
            break_chance = 1.0

            for i in range(row.slots_left):
                chance_card_is_played = (len(possible_cards) - i) / (total_cards_remaining - i)
                break_chance = break_chance * chance_card_is_played

            return break_chance * (row.points + est_pts_left)

    def _weighCardForBreak(self, card: int, rows: list[RowInfo]):
        """Give the expected points of this card for breaking (taking a row)"""
        cards_below_this = len(self.card_counter.getCardsInRange(1, card))
        cards_remaining = self.card_counter.getNumberOfCardsRemaining()

        # Ratio of remaining cards below our card
        ratio_below_this = cards_below_this / cards_remaining

        # For now, we naively assume we will just take the min row.
        min_row_score = min([r.points for r in rows])

        # If there are more cards below ours, then this card is less likely to break
        break_chance = (1.0 - ratio_below_this)
        return break_chance * min_row_score

    def chooseRow(self, card: int, rows: list[list[int]], cardsPlayed: list[int]) -> int:
        row_infos = RowInfo.CreateFromRowList(rows, self.card_counter)
        cards_left = [c for c in cardsPlayed if c > card]

        row_to_take = 0
        row_rating = 0

        for i in range(len(rows)):
            # If we were to take this row, where would the other cards resolve?
            hypothetical_rows = copy.deepcopy(row_infos)
            cur_row = hypothetical_rows[i]
            cur_pts_taken = cur_row.resolveCard(card, True)
            cur_pts_given = 0            

            RowInfo.UpdateRows(hypothetical_rows, self.card_counter)

            for c in cards_left:
                row = ResolveRow(c, hypothetical_rows)
                cur_pts_given += row.resolveCard(c, False)
                RowInfo.UpdateRows(hypothetical_rows, self.card_counter)

            # Evaluate the rows based on amount of points given vs. taken.
            # Add a little bit of fudge so we weight fewer points taken as a higher number

            # In aggressive mode, weigh giving points more heavily
            if (self.strategy == Strategy.AGGRESSIVE):
                cur_pts_given = cur_pts_given * 1.25

            cur_rating = (cur_pts_given + 0.001) / cur_pts_taken

            if cur_rating > row_rating:
                row_to_take = i
                row_rating = cur_rating
        
        return row_to_take
                

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
    ai.min_score = min([s[1] for s in scores])
    ai.max_score = max([s[1] for s in scores])
    ai.our_score = scores[0][1]

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
    ai.countCards(cardsPlayed)

    # TODO: we could weigh scores here and be more vindictive if we were winning
    return ai.chooseRow(card, rows, cardsPlayed)
