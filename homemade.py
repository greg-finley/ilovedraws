from __future__ import annotations
import chess
from chess.engine import PlayResult, Limit
import random
from lib.engine_wrapper import MinimalEngine, MOVE
from typing import Any
import logging


# Use this logger variable to print messages to the console or log files.
# logger.info("message") will always print "message" to the console or log file.
# logger.debug("message") will only print "message" if verbose logging is enabled.
logger = logging.getLogger(__name__)


class ExampleEngine(MinimalEngine):
    """An example engine that all homemade engines inherit."""

    pass


class ILoveDraws(ExampleEngine):

    def __init__(
        self,
        commands: COMMANDS_TYPE,
        options: OPTIONS_TYPE,
        stderr: Optional[int],
        draw_or_resign: Configuration,
        game: Optional[model.Game],
        **popen_args: str,
    ):
        super().__init__(commands, options, stderr, draw_or_resign, game, **popen_args)
        self.stockfish = chess.engine.SimpleEngine.popen_uci("./TEMP/sf")
        self.minimal_drawishness = 10  # centipawns

    def evaluate(self, board, timeLimit=0.1):
        result = self.stockfish.analyse(
            board, chess.engine.Limit(time=timeLimit - 0.01)
        )
        return result["score"].relative

    def search(self, board: chess.Board, time_left, *args) -> chess.engine.PlayResult:
        # Get amount of legal moves
        legalMoves = list(board.legal_moves)
        # Shuffle the moves to make the bot less predictable
        random.shuffle(legalMoves)

        # Base search time per move in seconds
        searchTime = 0.1

        # If the engine will search for more than 10% of the remaining time, then shorten it
        # to be 10% of the remaining time
        # Also, dont do this on the first move (because of weird behaviour with timeLeft being a Limit on first move)
        if type(time_left) != chess.engine.Limit:
            time_left /= 1000  # Convert to seconds
            if len(legalMoves) * searchTime > time_left / 10:
                searchTime = (time_left / 10) / len(legalMoves)

        # Initialise variables
        mostDrawishEvaluation = None
        mostDrawishMoves = []
        allEvaluations = []

        # Evaluate each move
        for move in legalMoves:
            # Play move
            board.push(move)

            # Evaluate position from opponent's perspective
            evaluation = self.evaluate(board, searchTime)
            evaluation_score = abs(evaluation.score(mate_score=10000))
            print("evaluation_score", evaluation_score)
            assert evaluation_score is not None
            allEvaluations.push(evaluation_score)

            # If the evaluation is less than the minimal_drawishness, return the move
            if evaluation_score <= self.minimal_drawishness:
                return PlayResult(move, None)

            # If the evaluation is more drawish than mostDrawishEvaluation, replace the mostDrawishMoves list with just this move
            if (
                mostDrawishEvaluation is None
                or mostDrawishEvaluation < evaluation_score
            ):
                mostDrawishEvaluation = evaluation_score
                mostDrawishMoves = [move]

            # If the evaluation is the same as mostDrawishEvaluation, add the move to the list
            elif mostDrawishEvaluation == evaluation_score:
                mostDrawishMoves.append(move)

            # Un-play the move, ready for the next loop
            board.pop()

        print("mostDrawishMoves", mostDrawishMoves)
        print("mostDrawishEvaluation", mostDrawishEvaluation)
        print("allEvaluations", allEvaluations)
        if mostDrawishMoves:
            move = random.choice(mostDrawishMoves)
        else:
            move = random.choice(legalMoves)

        return PlayResult(move, None)
