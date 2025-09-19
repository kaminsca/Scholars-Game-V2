import random
import pprint

from player import *
from actions import *

EXTRA_VERBOSE = False

class Game:
    def __init__(self):
        self.reset()

    def reset(self, evaluated_player=0):
        self.players = [Player(), Player()]
        self.current_player = 0
        self.evaluated_player = evaluated_player
        return self.game_state()
    
    def set_game_state(self, new_state):
        self.players[0].apply_encoded_state(new_state[0:2])
        self.players[1].apply_encoded_state(new_state[2:4])
        self.current_player = new_state[4]

    def game_state(self):
        player1 = self.players[0].encode_state()
        player2 = self.players[1].encode_state()
        observation = player1 + player2
        observation.append(self.current_player)
        return tuple(observation)

    def is_done(self):
        return not self.players[0].is_alive() or not self.players[1].is_alive()

    def get_winner(self):
        if self.players[0].is_alive() and not self.players[1].is_alive():
            return 0
        elif self.players[1].is_alive() and not self.players[0].is_alive():
            return 1
        return -1
    
    def print_players(self):
        print('P1:')
        self.players[0].print_player()
        print('P2:')
        self.players[1].print_player()

    # def step(self, action: Action):
    #     self.apply_action(action)
    #     if self.extra_action_required:
    #         self.current_player = self.extra_action_player
    #         self.extra_action_required = False
    #     else:
    #         self.current_player = 1 - self.current_player
    
    def apply_action(self, action: Action):
        if EXTRA_VERBOSE:
            print('chosen action: ', action)

        player = self.players[self.current_player]
        player_index = self.current_player
        opponent = self.players[1 - self.current_player]
        opponent_index = 1-player_index
        next_player = opponent_index
        

        if action.action_type == 'add':
            src_hand = player.get_hands()[action.source]
            target = opponent.get_hands()[action.targets[0] - 2]
            # shift the range from 1–5 0–4 before the modulo, then add 1 after
            target.value = (target.value + src_hand.value - 1) % 5 + 1
            # Opponent must immediately choose its state if 4 or 5
            if target.value > 3:
                target.state = 2


        elif action.action_type == 'redistribute':
            values = action.params['values']
            player.get_hands()[0].value = values[0]
            player.get_hands()[1].value = values[1]
            # Cur player must immediately choose its state if either hand is 4 or 5
            if player.get_hands()[0].value > 3:
                player.get_hands()[0].state = 2
                next_player = player_index
            if player.get_hands()[1].value > 3:
                player.get_hands()[1].state = 2
                next_player = player_index

        elif action.action_type == 'special':
            index = action.targets[0]
            if action.params['ability'] == 'plumb':
                if index > 1:
                    target = opponent.get_hands()[index - 2]
                else:
                    target = player.get_hands()[index]
                target.alive = 0
            elif action.params['ability'] == 'scissors':
                if index > 1:
                    target = opponent.get_hands()[index - 2]
                else:
                    target = player.get_hands()[index]
                if target.value == 1:
                    target.value = 5
                    target.state = 0
                else:
                    target.alive = 0
            elif action.params['ability'] == 'paper':
                if index > 1:
                    target = opponent.get_hands()[index - 2]
                else:
                    target = player.get_hands()[index]
                target.alive = 0
            elif action.params['ability'] == 'rock':
                if index > 1:
                    target = opponent.get_hands()[index - 2]
                else:
                    target = player.get_hands()[index]
                target.alive = 0
            elif action.params['ability'] == 'scissors_plumb':
                for index in action.targets:
                    if index > 1:
                        target = opponent.get_hands()[index - 2]
                    else:
                        target = player.get_hands()[index]
                    target.alive = 0
            elif action.params['ability'] == '3_scissors':
                for index in action.targets:
                    if index > 1:
                        target = opponent.get_hands()[index - 2]
                    else:
                        target = player.get_hands()[index]
                    if target.value == 1:
                        target.value = 5
                        target.state = 0
                    else:
                        target.alive = 0
                
        elif action.action_type == 'switch':
            player.get_hands()[action.source].state = 1 - player.get_hands()[action.source].state

        elif action.action_type == 'form':
            # prev hand state MUST have been either 2 or 3 (pending)
            prev_hand_state = player.get_hands()[action.source].state
            if prev_hand_state not in [2,3]:
                print('PREV HAND STATE ISSUE -- FORM CHANGE WAS NOT FROM 2 OR 3')
            player.get_hands()[action.source].state = action.params['form']
            if prev_hand_state == 2:
                next_player = player_index


        # Step game state to next player
        self.current_player = next_player

