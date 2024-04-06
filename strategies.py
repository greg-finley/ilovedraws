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


# Strategy names and ideas from tom7's excellent eloWorld video


class RandomMove(ExampleEngine):
    def search(self, board, *args):
        return random.choice(list(board.legal_moves))


class Alphabetical(ExampleEngine):
    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=board.san)
        return moves[0]


class FirstMove(ExampleEngine):
    """Gets the first move when sorted by uci representation"""

    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=str)
        return moves[0]


class WorstFish(ExampleEngine):

    def __init__(self, *args):
        self.stockfish = chess.engine.SimpleEngine.popen_uci(stockfishPath)
        super().__init__(*args)

    def evaluate(self, board, timeLimit=0.1):
        result = self.stockfish.analyse(
            board, chess.engine.Limit(time=timeLimit - 0.01)
        )
        return result["score"].relative

    def search(self, board: chess.Board, timeLeft, *args):
        # Get amount of legal moves
        legalMoves = tuple(board.legal_moves)

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
        worstEvaluation = None
        worstMoves = []

        # Evaluate each move
        for move in legalMoves:
            # Record if the move is a capture
            move.isCapture = board.is_capture(move)

            # Play move
            board.push(move)

            # Record if the move is a check
            move.isCheck = board.is_check()

            # Evaluate position from opponent's perspective
            evaluation = self.evaluate(board, searchTime)

            # If the evaluation is better than worstEvaluation, replace the worstMoves list with just this move
            if worstEvaluation is None or worstEvaluation < evaluation:
                worstEvaluation = evaluation
                worstMoves = [move]

            # If the evaluation is the same as worstEvaluation, append the move to worstMoves
            elif worstEvaluation == evaluation:
                worstMoves.append(move)

            # Un-play the move, ready for the next loop
            board.pop()

        # Categorise the moves into captures, checks, and neither
        worstCaptures = []
        worstChecks = []
        worstOther = []

        for move in worstMoves:
            if move.isCapture:
                worstCaptures.append(move)
            elif move.isCheck:
                worstChecks.append(move)
            else:
                worstOther.append(move)

        # Play a random move, preferring moves first from Other, then from Checks, then from Captures
        if len(worstOther) != 0:
            return random.choice(worstOther)
        elif len(worstChecks) != 0:
            return random.choice(worstChecks)
        else:
            return random.choice(worstCaptures)

    def quit(self):
        self.stockfish.close()
