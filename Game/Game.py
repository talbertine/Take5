# Game.py
# Runs a game of Take 5
# By Thomas Albertine

import random
import copy
from typing import Callable

class Game:
    """Represents a single game of Take 5"""
    NUM_CARDS = 104
    HAND_SIZE = 10
    NUM_ROWS = 4
    ROW_SIZE = 5
    TARGET_SCORE = 66

    def __init__(self, playerCount, seed=None, log=None):
        """Take 5 Game constructor"""
        # stash the current random state while we set up the game's random state
        extState = random.getstate()
        # If we don't care about the seed, use the current time as the seed.
        if seed is None:
            random.seed()
        else:
            random.seed(seed)
        # Save the random state we will use for random operations involving 
        # the game objects. That way, we can prevent AI players from messing 
        # with the randomness used by the game as a whole
        self.randomState = random.getstate()
        random.setstate(extState)

        # Create a number of player slots
        self.players = [Player() for _ in range(playerCount)]

        # Show that this exists, although we don't need to actually create it until the start of the game
        self.rows = None

    def prepareNewGame(self):
        # Initializes players
        for player in self.players:
            player.pregameSetup(len(self.players))

        self.log = []
        self.appendLog("\nGame Begun")
        
    def appendLog(self, message):
        self.log.append(message)

    def getLog(self):
        try:
            return self.log
        except NameError:
            return []

    def _formatRows(self):
        rowString = ""
        for row in self.rows:
            rowString += "\n\t" + ", ".join(map(lambda x: Game._formatCard(x), row))
        return rowString

    def prepareRound(self):
        """Prepares a new game with the current set of players"""
        self.appendLog("\nRound Begun")
        # Stash external random state, load game random state
        extState = random.getstate()
        random.setstate(self.randomState)

        # Create a deck of cards from 1 to 104, and shuffle it
        self.deck = [x for x in range(1, Game.NUM_CARDS + 1)]
        random.shuffle(self.deck)
        
        # Create a structure for the four rows in which cards will be played
        self.rows = [[] for _ in range(Game.NUM_ROWS)]
        # Put a card at the start of the row
        self.appendLog("\nInitial Rows:")
        for row in self.rows:
            card = self.deck.pop(0)
            row.append(card)
        self.appendLog(self._formatRows())

        # Deal out ten cards to everyone
        self.appendLog("\nPlayer Starting Hands:")
        for player in self.players:
            hand = self.deck[:Game.HAND_SIZE]
            self.deck = self.deck[Game.HAND_SIZE:]
            player.setHand(hand)
            self.appendLog("\n" + player.getName() + ": " + ", ".join(map(lambda x: Game._formatCard(x), hand)))

        # Revert to external random state
        self.randomState = random.getstate()
        random.setstate(extState)

    def getScoreList(self):
        """Gets a list of the player's scores, in player order"""
        scoreList = []
        for player in self.players:
            scoreList.append((player.getName(), player.getScore()))
        return scoreList

    def playGame(self):
        self.prepareNewGame()

        while True:
            self.prepareRound()
            for _ in range(Game.HAND_SIZE):
                self.appendLog("\nHand Begun")
                # prepare a list of scores for each player
                scoreList = self.getScoreList()

                actions = []
                cardsPlayed = []
                for player in self.players:
                    # save each player's action and keep it associated with them
                    card = player.playTurn(self.rows, scoreList)
                    actions.append((card, player, copy.copy(scoreList)))
                    cardsPlayed.append(card)
                    # Cycle the score list so that the first entry is always the current player's 
                    scoreList.append(scoreList.pop(0))

                # sort in ascending order, so that we know which goes first
                actions.sort(key=lambda x: x[0])

                #If a player played a card lower than all the ends of the rows, they get to clear a row of their choosing
                lowestRow = min([row[-1] for row in self.rows])
                if actions[0][0] < lowestRow:
                    card = actions[0][0]
                    player = actions[0][1]
                    thisScoreList = actions[0][2]
                    self.appendLog("\n" + player.getName() + " played " + Game._formatCard(card))

                    playedCards = list(map(lambda x: x[0], actions))
                    rowToBreak = player.breakRow(self.rows,thisScoreList, card, playedCards)
                    self.appendLog("\n" + player.getName() + " chose row " + str(rowToBreak))

                    # Add those points to the player
                    for oldCard in self.rows[rowToBreak]:
                        self.appendLog("\n" + player.getName() + " scored " + Game._formatCard(oldCard))
                        player.addScore(Game._cardToPoints(oldCard))

                    # Restart the row
                    self.rows[rowToBreak] = [card]
                
                    # Remove that action from the queue
                    actions.pop(0)

                # Now handle the remaining player's actions
                for card, player, _ in actions:
                    result = self.placeCard(card)
                    self.appendLog("\n" + player.getName() + " played " + Game._formatCard(card))
                    if not result is None:
                        # A row broke
                        oldRow = self.rows[result][:Game.ROW_SIZE]
                        self.rows[result] = self.rows[result][Game.ROW_SIZE:]
                        for oldCard in oldRow:
                            self.appendLog("\n" + player.getName() + " scored " + Game._formatCard(oldCard))
                            player.addScore(Game._cardToPoints(oldCard))
                self.appendLog("\nTurn Ended")
                # A hand has ended
                scoreList = self.getScoreList()
                for player in self.players:
                    # Notify each player of the results
                    player.endTurn(cardsPlayed, scoreList)
                    # Cycle the score list so that the first entry is always the current player's 
                    cardsPlayed.append(cardsPlayed.pop(0))
                    scoreList.append(scoreList.pop(0))
            self.appendLog("\nRound Ended")
            # a round has ended
            scoreList = self.getScoreList()
            for player in self.players:
                # Notify each player of the results
                player.endRound(scoreList)
                # Cycle the score list so that the first entry is always the current player's 
                scoreList.append(scoreList.pop(0))
            largestScore = max(map(lambda x: x.getScore(), self.players))
            if (largestScore > Game.TARGET_SCORE):
                # Somebody hit the target score, so the game is over
                break
        self.appendLog("\nGame Ended")
        # The game is over
        scoreList = self.getScoreList()
        for player in self.players:
            # Notify each player of the results
            player.endGame(scoreList)
            # Cycle the score list so that the first entry is always the current player's 
            scoreList.append(scoreList.pop(0))
        self.appendLog("\nFinal Scores:")
        for name, score in self.getScoreList():
            self.appendLog("\n" + name + ": " + str(score))
        return scoreList

    def placeCard(self, card):
        """Places the card in it's appropriate row. Returns the row that broke, if any"""
        bestRow = None
        distance = Game.NUM_CARDS # larger than the largest possible distance
        for i, row in enumerate(self.rows):
            thisDist = card - row[-1]
            if thisDist < 0:
                # If the end of the row is bigger than the card, it can't go here
                continue
            if thisDist < distance:
                # This is closer than the best one we've seen so far
                bestRow = i
                distance = thisDist
        self.rows[bestRow].append(card)
        if len(self.rows[bestRow]) > Game.ROW_SIZE:
            # the row broke
            return bestRow
        return None
    
    @classmethod
    def _formatCard(cls, card):
        return str(card) + "(" + str(Game._cardToPoints(card)) + ")"

    @classmethod
    def _cardToPoints(cls, card):
        score = 1
        if card % 5 == 0:
            # divisible by 5
            score += 1
        if card % 10 == 0:
            # divisible by 10
            score += 1
        if card % 11 == 0:
            # divisible by 11
            score += 4
        if card == 55:
            score += 1
        return score
        
    def getPlayers(self):
        """Returns a list of players
        The list is a copy so you can't remove them, but the references to the players are real, so be careful"""
        return copy.copy(self.players)

class Player:
    """A player object
    Organizes and contains objects relevant to players.
    Contains register and callback operations to allow us to isolate player choice from player housekeeping"""

    def __init__(self):
        """Player constructor"""
        self.resetCallbacks()
        self.aiState = None
        self.name = ""

    def resetCallbacks(self):
        self.setupCallback = None
        self.turnCallback = None
        self.breakCallback = None
        self.endRoundCallback = None
        self.endGameCallback = None
        self.endTurnCallback = None

    def setName(self, name : str):
        """Allows the player to set the name"""
        self.name = name

    def getName(self):
        if self.name.lower() == "cedar":
            return "That's Cedar!"
        return self.name

    def setHand(self, hand : list[int]):
        """Sets the player's hand"""
        self.hand = hand
        self.hand.sort()

    def setSetupCallback(self, callback):
        """Sets the optional callback which will happen at the start of the game, so that the AI modules can initialize their state
        Callback will receive only the number of players, and return an object containing any state needed during the player's turn"""
        self.setupCallback = callback

    def pregameSetup(self, numberOfPlayers):
        """Initializes anything that should happen at the start of the game """
        if not self.setupCallback is None:
            self.aiState = self.setupCallback(numberOfPlayers)
        self.score = 0

    def getScore(self):
        return self.score

    def addScore(self, points):
        self.score += points

    def setTurnCallback(self, callback):
        """Sets the callback which will happen when it's this player's turn
        Callback will receive:
            the AI state object, 
            a copy of the player's hand (should be sorted in order), 
            a copy of the rows as they are at the start of the turn, 
            and a list of tuples representing the player's name and score in that order, starting with the current player
        Callback should return the number on the card which is to be played"""
        self.turnCallback = callback

    def playTurn(self, rows, scores):
        """Allows the player to choose a card to play"""
        card = None
        while card is None:
            try:
                card = int(self.turnCallback(self.aiState, copy.copy(self.hand), copy.deepcopy(rows), copy.deepcopy(scores)))
                # Only allow cards in the player's hand
                if not card in self.hand:
                    print(str(card) + " is not in your hand.")
                    card = None
            except ValueError:
                print("Please enter your card of choice as an integer")
        self.hand.remove(card)
        return card

    def setBreakCallback(self, callback):
        """Sets the callback which will happen when the player plays a card lower than the ends of all the rows
        Callback will receive:
            The AI state object
            the card which was played
            a copy of the player's hand (should be sorted in order)
            a copy of the rows as they currently are
            everyone's played cards
            and a list of tuples representing the player's name and score in that order, starting with the current player
        Callback should return the index of the row to clear"""
        self.breakCallback = callback

    def breakRow(self, rows, scores, card, playedCards):
        """Allows the player to choose which row to claim, if they play a card lower than all the ends of the rows"""
        row = None
        while row is None:
            try:
                row = int(self.breakCallback(self.aiState, card, copy.copy(self.hand), copy.deepcopy(rows), copy.copy(playedCards), copy.copy(scores)))
                if row < 0 or row > Game.NUM_ROWS - 1:
                    print(str(row) + " is not a valid row. Please choose one between 0 and " + str(Game.NUM_ROWS - 1))
                    row = None
            except ValueError:
                print("Please enter your row of choice as an integer")
        return row

    def setEndGameCallback(self, callback):
        """Sets the optional callback which will happend at the end of the game, for displaying the results, or training a machine learning model
        Callback will receive:
            The AI state object
            and a list of tuples representing the player's name and score in that order, starting with the current player"""
        self.endGameCallback = callback

    def endGame(self, score):
        if not self.endGameCallback is None:
            self.endGameCallback(self.aiState, copy.deepcopy(score))

    def setEndRoundCallback(self, callback):
        """Sets an optional callback which will notify you when a round has ended. Useful if you're counting cards, for example.
        Callback will receive:
            The AI state object
            and a list of tuples representing the player's name and score in that order, starting with the current player"""
        
        self.endRoundCallback = callback

    def endRound(self, scores):
        if not self.endRoundCallback is None:
            self.endRoundCallback(self.aiState, copy.deepcopy(scores))

    def setEndTurnCallback(self, callback):
        """Sets an optional callback which will notify you when a hand has ended, and tell you what everyone ended up playing
        Callback will receive:
            The AI state object
            a list of cards people played, starting with the current player
            and a list of tuples representing the player's name and score in that order, starting with the current player"""
        self.endTurnCallback = callback

    def endTurn(self, playedCards, scoreList):
        if not self.endTurnCallback is None:
            self.endTurnCallback(self.aiState, copy.copy(playedCards), copy.deepcopy(scoreList))


