# Fixes the type hinting for 'list[int]'.
from __future__ import annotations

# ThomasBot.py
# An AI module that plays roughly the way I do. A little more naively, but better at counting cards
# It would be fun to do a massive dynamic programming table, but that sounds like it might be painful for anyone running the program
# By Thomas Albertine
import copy
import Game.Game

# Setup()
#   Used to initialize an AI state required later. Optional.
# Takes arguments:
#   Number of players
# Returns optionally an object containing the AI's state
def Setup(playerCount):
    return ThomasAIState()

# PostGame()
#   Used to present results, or to use results to train machine learning models, etc. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

# Not needed

# PostRound()
#   Used notify that a round is over, and that the cards will be reshuffled and dealt out again. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

def PostRound(ai, _):
    ai.reset()
            
# PostTurn()
#   Used notify that a turn is over, and which cards everyone has played. Useful if you're trying to count cards. Optional.
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of the players cards in player order starting with the current player
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player

def PostTurn(ai, playedCards, _):
    for card in playedCards:
        ai.seeCard(card)

# PlayCard()
#   Determines which card from the player's hand they should play
# Takes arguments:
#   The player AI object, or None if no such object was created
#   A list of cards in the player's hand, sorted in ascending order
#   A list of lists representing the current state of the card rows
#   A list of the players scores in player order formatted as a tuple (name, score) starting with the current player
# Returns a card in the player's hand that they intend to play
def PlayCard(ai, hand : list[int], rows, scores):
    if not ai.sawStartingCards:
        # We haven't counted the starting cards yet
        for row in rows:
            ai.seeCard(row[0])
        ai.sawStartingCards = True

        # While we're at it, we know no one else will play cards from our hand
        for card in hand:
            ai.seeCard(card, True)

    handBackup = copy.copy(hand)
    # break the hand into cards below the lowest end card and cards above it
    lowestEndCard = 105
    for row in rows:
        if lowestEndCard > row[-1]:
            lowestEndCard = row[-1]
    lowCards = []
    highCards = []
    for card in hand:
        if card < lowestEndCard:
            lowCards.append(card)
        else:
            highCards.append(card)

    # Is there an opportunity to sow some chaos for cheap?
    if len(lowCards) > 0:
        chaosPlay, indexToClaim = sowChaos(rows, lowCards, len(scores))
        if not chaosPlay is None:
            ai.queueAttack(indexToClaim)
            return chaosPlay

    
    if len(highCards) > 0:
        # split the cards into ones we think will break and ones we don't
        willBreak = []
        wontbreak = []
        for card in highCards:
            if willItBreak(rows, card, len(scores)):
                willBreak.append(card)
            else:
                wontbreak.append(card)
        if len(wontbreak) > 0:
            # We can play a card that we don't think will break a row
            # We want to play the one that has the fewest unseen cards between it and the end of the row it's going to
            # That way we minimize surprises
            return playItSafe(rows, wontbreak, ai)
        if len(willBreak) > 0:
            # We can't play a card that we feel safe about. Go for the Hail Mary, and just try to put as much space between us and the end of the row
            # in the hopes that some poor sap will play there first and bail us out
            return hailMary(rows, willBreak, ai)
    
    # If we get here, we have no good moves. Our cards are all lower than the lowest row, but it's not cheap enough to try to sow chaos, so just play low. 
    # Maybe the value won't spike too much
    handBackup.sort()
    return handBackup[0]


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
    # Always choose the cheapest row. 
    # We've either already planned to play the cheapest row as part of an offensive strategy, or we've been forced here and we're doing damage control
    indexToClaim = ai.getQueuedAttack()
    if not indexToClaim is None:
        return indexToClaim

    cheapestCost = 100
    cheapestIndex = -1

    for i, row in enumerate(rows):
        cost = Game.Game.Game.getTotalPoints(row)
        if cost < cheapestCost:
            cheapestCost = cost
            cheapestIndex = i
    return cheapestIndex

##########################################################

class ThomasAIState:

    def __init__(self):
        self.reset()

    def seeCard(self, card, isHandCard=False):
        self.playedCards.add(card)
        if not isHandCard:
            self.cardsUnaccountedFor -= 1

    def reset(self):
        self.isAttackQueued = False
        self.playedCards = set()
        self.sawStartingCards = False
        self.cardsUnaccountedFor = Game.Game.Game.NUM_CARDS

    def numUnseenCardsBetweenPair(self, lowCard, highCard):
        cardCount = 0
        for card in range(lowCard + 1, highCard):
            if not card in self.playedCards:
                cardCount += 1
        return cardCount

    def queueAttack(self, rowToClaim):
        self.isAttackQueued = True
        self.queuedAttack = rowToClaim

    def getQueuedAttack(self):
        if self.isAttackQueued:
            self.isAttackQueued = False
            return self.queuedAttack
        return None

def predictRow(rows, card):
    foundRow = -1
    distance = 104
    for i, row in enumerate(rows):
        if card < row[-1]:
            # It can't go in this row
            continue
        newDistance = card - row[-1]
        if newDistance < distance:
            distance = newDistance
            foundRow = i
    return foundRow

def willItBreak(rows, card, numPlayers):
    dest = predictRow(rows, card)
    slots = Game.Game.Game.ROW_SIZE - len(rows[dest])
    if slots >= numPlayers:
        # There aren't enough cards to make this row break
        return False

    if slots == 0:
        # This row will always break
        return True
    if slots == 1:
        return card - rows[dest][-1] > 5
    if slots == 2:
        return card - rows[dest][-1] > 10
    if slots == 3:
        return card - rows[dest][-1] > 20
    if slots == 4: 
        return card - rows[dest][-1] > 30
    # shouldn't ever get here, but oh well
    return False

def sowChaos(rows, lowCards, numPlayers):
    cheapestCost = 100
    cheapestIndices = {}

    for i, row in enumerate(rows):
        cost = Game.Game.Game.getTotalPoints(row)
        if cost < cheapestCost:
            cheapestCost = cost
            cheapestIndices = {i}
        elif cost == cheapestCost:
            cheapestIndices.add(i)

    # If we take the cheapest row, cards going to it will go to the highest row below it. We need to make sure that one's a risky play
    for cheapestIndex in cheapestIndices:
        # Find out which row cards will end up in
        targetindex = predictRow(rows, rows[cheapestIndex][-1] - 1)
        # If there is a valid target row, 
        if targetindex != -1:
            slots = Game.Game.Game.ROW_SIZE - len(rows[targetindex])
            # and it's volatile, meaning there's enough players that it's risky to play on.
            # and the row we want to take is fairly cheap itself
            if slots * 2 <= numPlayers - 1 and cheapestCost < 3:
                # go ahead and play low. We'll take the cheap row and force other players to the expensive one
                lowCards.sort()
                return lowCards[0], cheapestIndex
    # Not the time to sow chaos
    return None, None

def playItSafe(rows, wontbreak, ai):
    distance = 104
    shortCard = {}
    for card in wontbreak:
        rowIndex = predictRow(rows, card)
        newDist = ai.numUnseenCardsBetweenPair(rows[rowIndex][-1], card)
        if newDist < distance:
            distance = newDist
            shortCard = {card}
        elif newDist == distance:
            shortCard.add(card)
    shortCard = list(shortCard)
    shortCard.sort()
    # all else being equal, play the lower card first. It's slightly harder to have another opportunity for that.
    return shortCard[0]

def hailMary(rows, willbreak, ai):
    distance = 0
    longCard = set()
    for card in willbreak:
        rowIndex = predictRow(rows, card)
        newDist = ai.numUnseenCardsBetweenPair(rows[rowIndex][-1], card)
        if newDist > distance:
            distance = newDist
            longCard = {card}
        elif newDist == distance:
            longCard.add(card)
    longCard = list(longCard)
    longCard.sort()
    # all else being equal, play the lower card first. It's slightly harder to have another opportunity for that.
    return longCard[0]
