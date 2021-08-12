# ===============================================================================
# Imports
# ===============================================================================

import time
import abstract
from players import simple_player

from collections import defaultdict

from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
from checkers.consts import EM, RK, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP, BOARD_ROWS, BOARD_COLS

# ===============================================================================
# Globals
# ===============================================================================

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5

# ===============================================================================
# Player
# ===============================================================================

class Player(simple_player.Player):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        simple_player.Player.__init__(self, setup_time, player_color, time_per_k_turns, k)

    def get_move(self, game_state, possible_moves):
        self.clock = time.process_time()
        self.time_for_current_move = self.get_time_for_current_move(game_state)
        if len(possible_moves) == 1:
            return possible_moves[0]

        current_depth = 1
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything
        minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time, self.selective_deepening_criterion)

        # Iterative deepening until the time runs out.
        while True:
            print('going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}'.format(current_depth, self.time_for_current_move - (time.process_time() - self.clock), prev_alpha, best_move))

            try:
                (alpha, move), run_time = run_with_limited_time(minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {}, self.time_for_current_move - (time.process_time() - self.clock))
            except (ExceededTimeError, MemoryError):
                print('no more time, achieved depth {}'.format(current_depth))
                break

            if self.no_more_time():
                print('no more time')
                break

            prev_alpha = alpha
            best_move = move

            if alpha == INFINITY:
                print('the move: {} will guarantee victory.'.format(best_move))
                break

            if alpha == -INFINITY:
                print('all is lost')
                break

            current_depth += 1

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.process_time() - self.clock)

        return best_move

    def get_time_for_current_move(self, state):
        possible_moves = state.get_possible_moves()

        piece_counts = defaultdict(lambda: 0)
        for loc_val in state.board.values():
            if loc_val != EM:
                piece_counts[loc_val] += 1

        my_pieces = piece_counts[PAWN_COLOR[self.color]]
        my_kings = piece_counts[KING_COLOR[self.color]]
        op_pieces = piece_counts[PAWN_COLOR[OPPONENT_COLOR[self.color]]]
        op_kings = piece_counts[KING_COLOR[OPPONENT_COLOR[self.color]]]

        my_u = my_pieces + my_kings
        op_u = op_pieces + op_kings
 
        # Checking whether the enemy have more soldiers than me and there are no kings on the board.
        if my_pieces < op_pieces and my_kings == 0 and op_kings == 0:
            if self.k <= 2:
                # If K is less or equals to 2 then we will divide by 2 since no need for more actions.
                return self.time_remaining_in_round / 2 - 0.05
            else:
                # Otherwise we'll divided by 3 the actions since we want to explore more to overcome the enemy.
                return self.time_remaining_in_round / 3 - 0.05
        # If the soldier amount and the king amount of the enemy is bigger then we will explore more to overcome the enemy.
        elif my_pieces < op_pieces and my_kings < op_kings:
            return self.time_remaining_in_round / 2 - 0.05
        # If there are no soldiers on the board and only kings we want to explore deeply to overcome the enemy.
        elif my_pieces == 0 and op_pieces == 0 and my_kings > op_kings:
            return self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        # Otherwise we'll divide uniformly.
        else:
            return self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

        return self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

    # Lea Methods Old.
    def get_time_for_current_move(self, state):
        possible_moves = state.get_possible_moves()
        piece_counts = defaultdict(lambda: 0)
        for loc_val in state.board.values():
            if loc_val != EM:
                piece_counts[loc_val] += 1
        opponent_color = OPPONENT_COLOR[self.color]

        my_pieces = piece_counts[PAWN_COLOR[self.color]]
        my_kings = piece_counts[KING_COLOR[self.color]]
        op_pieces = piece_counts[PAWN_COLOR[opponent_color]]
        op_kings = piece_counts[KING_COLOR[opponent_color]]

        my_u = my_pieces + my_kings         
        op_u = op_pieces + op_kings

        if op_kings > my_kings and op_u > my_u:
            return self.time_remaining_in_round / 1.5 - 0.05
        elif len(possible_moves) < 2:
            return self.time_remaining_in_round / 3 - 0.05
        elif self.pawn_close_to_op_king(state) == True:
            return self.time_remaining_in_round / 2 - 0.05

        return self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

    def pawn_close_to_op_king(self, state):
        my_pawn_list = []
        op_king_list = []

        for loc_val in state.board.items():
            if loc_val[1] != EM:
                if loc_val[1] == PAWN_COLOR[self.color]:
                    my_pawn_list.append(loc_val[0])
                if loc_val[1] == KING_COLOR[OPPONENT_COLOR[self.color]]:
                    op_king_list.append(loc_val[0])

        if len(my_pawn_list) == 0 or len(op_king_list) == 0:
            return False
        
        for my_pawn_loc in my_pawn_list:
            for op_king_loc in op_king_list:
                distance = sqrt((my_pawn_loc[0] - op_king_loc[0]) ** 2 + (my_pawn_loc[1] - op_king_loc[1]) ** 2)
                if distance < 2:
                    return True
        return False

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'improved')

# c:\python35\python.exe run_game.py 2 10 5 y improved_player random_player
