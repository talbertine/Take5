# userInput.py
# An "AI" module that just asks the user for the choices it should make, in case you want to play along too
# By Thomas Albertine
from colorama import just_fix_windows_console
just_fix_windows_console()
from colorama import Fore, Back, Style

import utils
from Game.Game import Game

# Setup()
#   Used to initialize an AI state required later. Optional.
# Takes arguments:
#   Number of players
# Returns optionally an object containing the AI's state

# Not needed for User Input

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

def PostRound(_, scoreList : list[tuple[str, int]]):
    print(Fore.YELLOW + "\nPost Round Scores: " + Style.RESET_ALL)
    for score in scoreList:
        print(str(score[1]) + "\t" + score[0])
            
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
# Returns a card in the player's hand that they intend to play. Will be converted to int with error checking, so we don't need to be too picky
def PlayCard(_, hand : list[int], rows : list[list[int]], scoreList : list[tuple[str, int]]) -> str:
    print(formatRows(Fore.YELLOW + "\nCurrent Rows: " + Style.RESET_ALL, rows, False))
    print(formatCardList(Fore.YELLOW + "Your Hand: " + Style.RESET_ALL, hand))
    # Caller does some error checking, so we don't have to be too thorough here. If it's not an int, we'll get reprompted
    return input("Which card would you like to play? ")

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
def ChooseRow(_, card : int, hand : list[int], rows : list[list[int]], cardsPlayed : list[int], scoreList : list[tuple[str, int]]):
    print(formatRows(Fore.YELLOW + "\nChoose a Row to Claim: " + Style.RESET_ALL, rows, True))
    print(formatCardList(Fore.YELLOW + "Cards Played This Round: " + Style.RESET_ALL, cardsPlayed))
    print(formatCardList(Fore.YELLOW + "Your Hand: " + Style.RESET_ALL, hand))
    return input("Which row would you like to claim? ")

##########################################
# Helper Functions, not in the interface #
##########################################

def formatRows(prompt : str, rows : list[list[int]], isIndexed : bool) -> str:
    result = prompt + "\n"
    result += Back.RED + "\t" + "\t".join(["1", "2", "3", "4", "5", "Break!"]) + Style.RESET_ALL + "\n"
    for i, row in enumerate(rows):
        if isIndexed:
            result += "(" + str(i) + ")"
        result += "\t" + "\t".join(map(lambda x: Game._formatCard(x), row)) + "\n"
    return result[:-1] 

def formatCardList(label : str, cardList : list[int]):
    result = label + "\n"
    result += "\t" + ", ".join(map(lambda x: Game._formatCard(x), cardList)) 
    return result
