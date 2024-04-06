"""
Some example strategies for people who want to create a custom, homemade bot.
And some handy classes to extend
"""

import sys
import chess
import chess.engine
import random
from engine_wrapper import EngineWrapper

if sys.platform == "win32":
    stockfishPath = "stockfish\\stockfish.exe"
else:
    stockfishPath = "stockfish/stockfish"


class FillerEngine:
    """
    Not meant to be an actual engine.

    This is only used to provide the property "self.engine"
    in "MinimalEngine" which extends "EngineWrapper"
    """

    def __init__(self, main_engine, name=None):
        self.id = {"name": name}
        self.name = name
        self.main_engine = main_engine

    def __getattr__(self, method_name):
        main_engine = self.main_engine

        def method(*args, **kwargs):
            nonlocal main_engine
            nonlocal method_name
            return main_engine.notify(method_name, *args, **kwargs)

        return method


class MinimalEngine(EngineWrapper):
    """
    Subclass this to prevent a few random errors

    Even though MinimalEngine extends EngineWrapper,
    you don't have to actually wrap an engine.

    At minimum, just implement `search`,
    however you can also change other methods like
    `notify`, `first_search`, `get_time_control`, etc.
    """

    def __init__(self, *args, name=None):
        super().__init__(*args)

        self.engine_name = self.__class__.__name__ if name is None else name

        self.last_move_info = []
        self.engine = FillerEngine(self, name=self.name)
        self.engine.id = {"name": self.engine_name}

    def search_with_ponder(self, board, wtime, btime, winc, binc, ponder):
        timeleft = 0
        if board.turn:
            timeleft = wtime
        else:
            timeleft = btime
        return self.search(board, timeleft, ponder)

    def search(self, board, timeleft, ponder):
        raise NotImplementedError("The search method is not implemented")

    def notify(self, method_name, *args, **kwargs):
        """
        The EngineWrapper class sometimes calls methods on "self.engine".
        "self.engine" is a filler property that notifies <self>
        whenever an attribute is called.

        Nothing happens unless the main engine does something.

        Simply put, the following code is equivalent
        self.engine.<method_name>(<*args>, <**kwargs>)
        self.notify(<method_name>, <*args>, <**kwargs>)
        """
        pass


class ExampleEngine(MinimalEngine):
    pass


class ILoveDraws(ExampleEngine):

    def __init__(self, *args):
        self.stockfish = chess.engine.SimpleEngine.popen_uci(stockfishPath)
        self.minimal_drawishness = 0.1
        super().__init__(*args)

    def evaluate(self, board, timeLimit=0.1):
        result = self.stockfish.analyse(
            board, chess.engine.Limit(time=timeLimit - 0.01)
        )
        return result["score"].relative

    def search(self, board: chess.Board, timeLeft, *args):
        # Get amount of legal moves
        legalMoves = list(board.legal_moves)
        # Shuffle the moves to make the bot less predictable
        random.shuffle(legalMoves)

        # Base search time per move in seconds
        searchTime = 0.1

        # If the engine will search for more than 10% of the remaining time, then shorten it
        # to be 10% of the remaining time
        # Also, dont do this on the first move (because of weird behaviour with timeLeft being a Limit on first move)
        if type(timeLeft) != chess.engine.Limit:
            timeLeft /= 1000  # Convert to seconds
            if len(legalMoves) * searchTime > timeLeft / 10:
                searchTime = (timeLeft / 10) / len(legalMoves)

        # Initialise variables
        mostDrawishEvaluation = None
        mostDrawishMoves = []

        # Evaluate each move
        for move in legalMoves:
            # Play move
            board.push(move)

            # Evaluate position from opponent's perspective
            evaluation = abs(self.evaluate(board, searchTime))

            # If the evaluation is less than the minimal_drawishness, return the move
            if evaluation <= self.minimal_drawishness:
                return move

            # If the evaluation is more drawish than mostDrawishEvaluation, replace the mostDrawishMoves list with just this move
            if mostDrawishEvaluation is None or mostDrawishEvaluation < evaluation:
                mostDrawishEvaluation = evaluation
                mostDrawishMoves = [move]

            # If the evaluation is the same as mostDrawishEvaluation, add the move to the list
            elif mostDrawishEvaluation == evaluation:
                mostDrawishMoves.append(move)

            # Un-play the move, ready for the next loop
            board.pop()

        return random.choice(mostDrawishMoves)

    def quit(self):
        self.stockfish.close()
