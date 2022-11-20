# Take5
A toy project to play a game of take 5, and to allow my friends to make little AI plugins

## How to Play
Simple! Just download the code and run Take5.py. It's in the root of the directory!

## Want to add your own AI module?
Almost as simple!

Just put a python file in the AIs folder, and make sure it implements the necessary functions.

* Required Functions
  * PlayCard(ai, hand, rows, scores)
    * On each turn, you will choose a card from your hand to play, simultaneously with the other players
    * ai is the AI state object that you may or may not have created in the setup function
    * hand is a list of integers representing your cards
    * rows is a list of lists of integers representing the four rows of up to 5 cards in which your played card will ultimately end up
    * scores is a list of tuples of each player's name and their score, starting with you
    * You will return the number on the card you wish to play
  * ChooseRow(ai, card, hand, rows, cardsPlayed, scores)
    * When you play a card lower than the last cards in all the rows, you must claim a row of your choosing for points.
    * ai is the AI state object that you may or may not have created in the setup function
    * card is an integer representing the card you played
    * hand is a list of integers representing your cards
    * rows is a list of lists of integers representing the four rows of up to 5 cards of which you may choose one to claim
    * cardsPlayed is a list of integers represnenting the cards everyone has played.
    * scores is a list of tuples of each player's name and their score, starting with you
    * You will return the index of the row you wish to claim
* Optional Functions
  * Setup(playerCount)
    * Setup gives you an opportunity to initialize any state that your AI may need
    * Player count is an integer representing the number of players
    * If you want an AI state object, you can return it from this function
  * PostTurn(ai, cards, scores)
    * This function is called at the end of each turn
    * ai is the AI state object that you may or may not have created in the setup function
    * cards is a list of cards that everyone has played this turn, which is useful for counting cards, for example
    * scores is a list of tuples of each player's name and their score, starting with you
  * PostRound(ai, scores)
    * This function is called at the end of each round, when we evalutate if the game is over, and when we deal out new cards to everyone.
    * ai is the AI state object that you may or may not have created in the setup function
    * scores is a list of tuples of each player's name and their score, starting with you
  * PostGame(ai, scores)
    * This function is called at the end of the game, in case you were doing some kind of machine learning or wanted to do something with the final results
    * ai is the AI state object that you may or may not have created in the setup function
    * scores is a list of tuples of each player's name and their score, starting with you
