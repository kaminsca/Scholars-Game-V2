import random
import pickle
import os
import pprint

from player import *
from game import *

class Agent():
    def __init__(self, alpha=0.1, gamma=0.95, epsilon=0.1, verbose = False, q_table_src='q_table.pkl'):
        self.Q = {}  # Q[(state_tuple, action_id)] = value
        self.epsilon = epsilon
        self.alpha = alpha # learning rate
        self.gamma = gamma # discount factor
        self.verbose = verbose
        self.q_table_src = q_table_src
        self.load_q_table()



    def select_action(self, state, valid_action_ids):
        # epsilon greedy
        if random.random() < self.epsilon:
            self.verbose_print('CHOSING RANDOM ACTION')
            return random.choice(valid_action_ids)

        # Choose best Q-value
        q_vals = [self.Q.get((state, a), 0.0) for a in valid_action_ids]
        max_q = max(q_vals)
        best_actions = [a for a, q in zip(valid_action_ids, q_vals) if q == max_q]
        return random.choice(best_actions)
    
    def train_q_learning(self, num_episodes=20, opponent_q_path=None):
        wins = 0
        draws = 0
        opponent_q_table = None
        if opponent_q_path and os.path.exists(opponent_q_path):
            with open(opponent_q_path, 'rb') as f:
                opponent_q_table = pickle.load(f)
            print(f"Q-table loaded from {opponent_q_path} with {len(opponent_q_table)} entries.")

        for episode in range(num_episodes):
            game = Game()
            state = game.reset(evaluated_player=episode%2)
            turn = 0
            prev_state = None
            prev_action_id = None

            while True:
                state = game.game_state()
                cur_player = game.current_player
                self.verbose_print(f"Turn {turn}: {game.game_state()}")
                player = game.players[cur_player]
                opponent = game.players[1 - cur_player]

                # check if need to choose value first: 

                valid_actions = get_valid_actions(player, opponent)
                valid = valid_actions['actions']
                encoded = valid_actions['encoded']

                if len(encoded) == 0:
                    break

                # select action
                if cur_player == game.evaluated_player:
                    # if want to evaluate policy without exploration, need to set epsilon to 0
                    action_id = self.select_action(state, encoded)
                    action = ID_TO_ACTION[action_id]
                # opp plays according to policy from opponent q table
                elif opponent_q_table:
                    # choose best Q-value
                    q_vals = [self.Q.get((state, a), 0.0) for a in encoded]
                    max_q = max(q_vals)
                    best_actions = [a for a, q in zip(encoded, q_vals) if q == max_q]
                    action_id = random.choice(best_actions)
                    action = ID_TO_ACTION[action_id]
                # playing against random policy opponent if no opponent q table
                else:
                    action_id = random.choice(encoded)
                    action = ID_TO_ACTION[action_id]

                # time t: select action A_t
                # game.step(action)
                game.apply_action(action)
                done = game.is_done()
                if turn > 300:
                    self.verbose_print('Max turns reached (300)')
                    draws += 1
                    done = True

                # enter new state S_t+1
                # observe reward R_t+1
                reward = 0
                if done:
                    if self.verbose: game.print_players()  
                    won_text = 'WON' if game.get_winner() == game.evaluated_player else 'LOST'
                    self.verbose_print(f"Game {episode} Winner: {game.get_winner()} ({won_text})\n")
                    if game.get_winner() == game.evaluated_player:
                        reward = 1
                        wins += 1
                    
                    else:
                        reward = -1
                    if cur_player != game.evaluated_player:
                        q_value = self.Q.get((prev_state, prev_action_id), 0.0)
                        self.Q[(prev_state, prev_action_id)] = (1 - self.alpha) * q_value + self.alpha * reward
                    else:
                        q_value = self.Q.get((state, action_id), 0.0)
                        self.Q[(state, action_id)] = (1 - self.alpha) * q_value + self.alpha * reward
                    break
                
                # Update Q if current player
                if cur_player == game.evaluated_player:
                    prev_state = state
                    prev_action_id = action_id
                    self.update_q_table(game, cur_player, 1-cur_player, state, action_id, reward)
                    
                turn += 1

            if (episode + 1) % 100 == 0:
                self.save_q_table()
                print(f"Wins/Games: {wins}/{episode + 1} ({draws} Draws)")


    """
    game: Game object
    cur: Player who just chose an action
    opp: Opposing player
    state: State before action was chosen
    action_id: Obviously the action that was chosen
    reward: Seems to be always 0 here hm.
    """
    def update_q_table(self, game, cur, opp, state, action_id, reward):
        next_state = game.game_state()
        # game state has already been updated to state after chosen action:
        # check if current player still has to take an action -- don't have to simulate opponent choice
        valid_next_actions = []
        if game.current_player == cur:
            valid_next_actions = get_valid_actions(
                game.players[game.current_player],
                game.players[game.current_player - 1]
            )['encoded']
            next_player_state = next_state
        else:
            # Simulate opponent action
            simulated_game = Game()
            simulated_game.set_game_state(next_state)
            while simulated_game.current_player != cur:
                # opponent takes a random move, next state will be the evaluated player's next state
                valid_actions = get_valid_actions(
                    simulated_game.players[simulated_game.current_player],
                    simulated_game.players[simulated_game.current_player - 1]
                )['encoded']
                other_player_action = ID_TO_ACTION[random.choice(valid_actions)]
                simulated_game.apply_action(other_player_action)

            # next state available for the evaluated player
            next_player_state = simulated_game.game_state()
            valid_next_actions = get_valid_actions(simulated_game.players[simulated_game.current_player], simulated_game.players[simulated_game.current_player - 1])['encoded']

        # get best Q[next state]:
        future_qs = []
        for act_id in valid_next_actions:
            future_qs.append(self.Q.get((next_player_state, act_id), 0.0))

        max_future_q = max(future_qs) if future_qs else 0

        q_st_at = self.Q.get((state, action_id), 0.0)

        self.Q[(state, action_id)] =  (1 - self.alpha) * q_st_at + self.alpha * (reward + self.gamma * max_future_q)
    
    def save_q_table(self):
        with open(self.q_table_src, 'wb') as f:
            pickle.dump(self.Q, f)

    def load_q_table(self):
        filename = self.q_table_src
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                self.Q = pickle.load(f)
            print(f"Q-table loaded from {filename} with {len(self.Q)} entries.")
        self.show_top_n_moves(3)
        self.show_bottom_n_moves(3)


    def show_top_n_moves(self, n=10):
        top_q = sorted(self.Q.items(), key=lambda x: -x[1])[:n]
        print(f"Top {n} moves")
        for (state, action_id), value in top_q:
            print(f"Q[{state}, {action_id}] = {value:.2f}")

    def show_top_n_moves_based_on_player(self, n=10, player=1):
        # Filter Q-table to only include entries where state[4] is 0 or 1
        filtered_q = {
            k: v for k, v in self.Q.items()
            if k[0][4] == player
        }

        # Sort the filtered Q-table by value descending
        top_q = sorted(filtered_q.items(), key=lambda x: -x[1])[:n]

        print(f"Top {n} moves where state[4] is {player}:")
        for (state, action_id), value in top_q:
            print(f"Q[{state}, {action_id}] = {value:.2f}")

    def show_state_value(self, state=(1,1,1,1,0)):
        # Find all (action, Q-value) pairs for the given state
        actions = [(action_id, value) for (s, action_id), value in self.Q.items() if s == state]

        if not actions:
            print(f"No Q-values found for state {state}.")
            return

        # Find the max Q-value
        max_value = max(value for _, value in actions)
        # Find all actions that have this max Q-value (in case of ties)
        best_actions = [action_id for action_id, value in actions if value == max_value]

        print(f"Value of state {state} = {max_value:.2f}")
        print(f"Best action(s): {best_actions}")
    
    def action_values_in_state(self, state=(1,1,1,1,0)):
        # Find all (action, Q-value) pairs for the given state
        actions = [(action_id, value) for (s, action_id), value in self.Q.items() if s == state]

        if not actions:
            print(f"No Q-values found for state {state}.")
            return
        
        actions.sort(key=lambda x: x[1], reverse=True)

        for action_id, value in actions:
            print(f"  {ID_TO_ACTION[action_id]}: ({value:.4f})")

    def show_bottom_n_moves(self, n=10):
        bot_q = sorted(self.Q.items(), key=lambda x: x[1])[:n]
        print(f"Bottom {n} moves")
        for (state, action_id), value in bot_q:
            print(f"Q[{state}, {action_id}] = {value:.2f}")

    def verbose_print(self, message):
        if self.verbose:
            print(message)