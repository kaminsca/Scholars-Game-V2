import json
from pprint import pprint
from player import *

ACTION_TYPES = ['add', 'redistribute', 'special']
SOURCE_HANDS = [0, 1]  # index of player's hands
TARGET_HANDS = [0, 1, 2, 3]  # 0/1 for own hands, 2/3 for opponent hands

class Action:
    def __init__(self, action_type, source=None, targets=None, params=None):
        self.action_type = action_type
        self.source = source
        self.targets = targets or []
        self.params = params or {}

    def to_dict(self):
        return {
            'action_type': self.action_type,
            'source': self.source,
            'targets': self.targets,
            'params': self.params,
        }

    def __eq__(self, other):
        def normalize_params(p):
            return {k: tuple(v) if isinstance(v, list) else v for k, v in p.items()}

        return (
            self.action_type == other.action_type and
            self.source == other.source and
            self.targets == other.targets and
            normalize_params(self.params) == normalize_params(other.params)
        )

    def __hash__(self):
        # Convert any list values in params to tuples for hashing
        hashable_params = frozenset(
            (k, tuple(v) if isinstance(v, list) else v)
            for k, v in self.params.items()
        )
        return hash((self.action_type, self.source, tuple(self.targets), hashable_params))

    def __repr__(self):
        return f"Action({self.action_type}, src={self.source}, tgt={self.targets}, params={self.params})"
    

ALL_ACTIONS = []
ACTION_TO_ID = {}
ID_TO_ACTION = {}

def generate_all_possible_actions():
    ALL_ACTIONS.clear()
    ACTION_TO_ID.clear()
    ID_TO_ACTION.clear()

    idx = 0

    # -- ADD actions --
    for src in SOURCE_HANDS:
        for target in [2,3]:
            action = Action('add', source=src, targets=[target])
            ALL_ACTIONS.append(action)
            ACTION_TO_ID[action] = idx
            ID_TO_ACTION[idx] = action
            idx += 1

    # -- REDISTRIBUTE actions --
    for total in range(2,9):
        for i in range(1, total):
            val1 = i
            val2 = total - i
            if val1 <= 5 and val2 <= 5:
                params = {'values': sorted([val1, val2])}
                action = Action('redistribute', source=None, targets=[], params=params)
                if action not in ACTION_TO_ID:
                    ALL_ACTIONS.append(action)
                    ACTION_TO_ID[action] = idx
                    ID_TO_ACTION[idx] = action
                    idx += 1

    # -- SWITCH actions --
    for src in SOURCE_HANDS:
        action = Action('switch', source=src)
        ALL_ACTIONS.append(action)
        ACTION_TO_ID[action] = idx
        ID_TO_ACTION[idx] = action
        idx += 1

    # -- SPECIAL actions --
    SINGLE_TARGET_SPECIAL = ['plumb', 'scissors', 'paper', 'rock']
    for src in SOURCE_HANDS:
        for tgt in TARGET_HANDS:
            if tgt == src:
                continue
            for special in SINGLE_TARGET_SPECIAL:
                action = Action('special', source=src, targets=[tgt], params={'ability': special})
                ALL_ACTIONS.append(action)
                ACTION_TO_ID[action] = idx
                ID_TO_ACTION[idx] = action
                idx += 1
    MULTI_TARGET_SPECIAL = ['scissors_plumb', '3_scissors']
    for src in SOURCE_HANDS:
        # all combinations of 2 other hands:
        other_hands = [h for h in TARGET_HANDS if h != src]
        for i in range(len(other_hands)):
            for j in range(i + 1, len(other_hands)):
                targets = [other_hands[i], other_hands[j]]
                for special in MULTI_TARGET_SPECIAL:
                    action = Action('special', source=src, targets=targets, params={'ability': special})
                    ALL_ACTIONS.append(action)
                    ACTION_TO_ID[action] = idx
                    ID_TO_ACTION[idx] = action
                    idx += 1

    # -- CHOOSE FORM actions --
    for src in SOURCE_HANDS:
        for form in [0,1]:
            action = Action('form', source=src, params={'form': form})
            ALL_ACTIONS.append(action)
            ACTION_TO_ID[action] = idx
            ID_TO_ACTION[idx] = action
            idx += 1
    save_actions_to_file()

def save_actions_to_file(filename="actions.json"):
    data = {
        "actions": [action.to_dict() for action in ALL_ACTIONS],
        "action_to_id": {str(idx): ACTION_TO_ID[action] for idx, action in enumerate(ALL_ACTIONS)},
        "id_to_action": {str(idx): action.to_dict() for idx, action in enumerate(ALL_ACTIONS)},
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_actions_from_file(filename="actions.json"):
    with open(filename, 'r') as f:
        data = json.load(f)

    for idx_str, action_data in data["id_to_action"].items():
        idx = int(idx_str)
        action = Action(**action_data)
        ALL_ACTIONS.append(action)
        ACTION_TO_ID[action] = idx
        ID_TO_ACTION[idx] = action


def get_valid_actions(curPlayer: Player, opponentPlayer: Player):
    load_actions_from_file()
    valid_actions = []

    curHands = curPlayer.get_hands()
    left = curHands[0]
    right = curHands[1]
    oppHands = opponentPlayer.get_hands()
    oppLeft = oppHands[0]
    oppRight = oppHands[1]
    
    # first check if either current hand needs to choose state:
    if hand_requires_state(left):
        valid_actions.append(Action('form', source=0, params={'form': 0}))
        valid_actions.append(Action('form', source=0, params={'form': 1}))
    elif hand_requires_state(right):
        valid_actions.append(Action('form', source=1, params={'form': 0}))
        valid_actions.append(Action('form', source=1, params={'form': 1}))
    else:
        valid_actions.extend(valid_actions_one_hand(left, right, oppLeft, oppRight, 0))
        # Same thing but for right hand
        valid_actions.extend(valid_actions_one_hand(right, left, oppLeft, oppRight, 1))

        # get valid redistribute actions
        if left.alive and right.alive:
            sum = left.value + right.value
            for i in range(1, sum):
                val1 = i
                val2 = sum - i
                if val1 > 5 or val2 > 5:
                    continue
                if sorted([left.value, right.value]) == sorted([val1, val2]):
                    continue
                # stop duplicates
                if val1 > val2:
                    break
                params = {'values': sorted([val1, val2])}
                valid_actions.append(Action('redistribute', source=None, targets=[], params=params))

    encoded_valid_actions = [action_to_id(action) for action in valid_actions]
    return {'actions': valid_actions, 'encoded': encoded_valid_actions}

def valid_actions_one_hand(hand, other_hand, opp_left, opp_right, source_index):
    valid_actions = []
    hand_map = {
        1-source_index: other_hand,
        2: opp_left,
        3: opp_right
    }
    # get all pairs of living hands (not including current hand)
    living = [(idx, h) for idx, h in hand_map.items() if h.alive]
    combinations = []
    for i in range(len(living)):
        for j in range(i + 1, len(living)):
            (index1, hand1) = living[i]
            (index2, hand2) = living[j]
            combinations.append((index1, index2))

    
    if hand.alive:
        # get valid add actions
        if hand.value < 5:
            if opp_left.alive:
                valid_actions.append(Action('add', source=source_index, targets=[2]))
            if opp_right.alive:
                valid_actions.append(Action('add', source=source_index, targets=[3]))

        # get valid switch actions
        if hand.value > 3:
            valid_actions.append(Action('switch', source=source_index))

        # get valid special actions
        if hand.value == 1:
            if hand_is_rock(other_hand):
                valid_actions.append(Action('special', source=source_index, targets=[1 - source_index], params={'ability': 'plumb'}))
            if hand_is_rock(opp_left):
                valid_actions.append(Action('special', source=source_index, targets=[2], params={'ability': 'plumb'}))
            if hand_is_rock(opp_right):
                valid_actions.append(Action('special', source=source_index, targets=[3], params={'ability': 'plumb'}))

        if hand.value == 2 or (hand.value == 4 and hand.state == 0):
            # cut
            if hand_is_paper(other_hand) or hand_is_boinger(other_hand):
                valid_actions.append(Action('special', source=source_index, targets=[1 - source_index], params={'ability': 'scissors'}))
            if hand_is_paper(opp_left) or hand_is_boinger(opp_left):
                valid_actions.append(Action('special', source=source_index, targets=[2], params={'ability': 'scissors'}))
            if hand_is_paper(opp_right) or hand_is_boinger(opp_right):
                valid_actions.append(Action('special', source=source_index, targets=[3], params={'ability': 'scissors'}))

        if hand.value == 3:
            # double cut
            for hand_pair in combinations:
                first = hand_map[hand_pair[0]]
                second = hand_map[hand_pair[1]]
                if (hand_is_paper(first) or hand_is_boinger(first)) and (hand_is_paper(second) or hand_is_boinger(second)):
                    valid_actions.append(Action('special', source=source_index, targets=[hand_pair[0], hand_pair[1]], params={'ability': '3_scissors'}))

        if hand.value == 2 or hand.value == 3:
            # double plumb
            for hand_pair in combinations:
                first = hand_map[hand_pair[0]]
                second = hand_map[hand_pair[1]]
                if hand_is_rock(first) and hand_is_rock(second):
                    valid_actions.append(Action('special', source=source_index, targets=[hand_pair[0], hand_pair[1]], params={'ability': 'scissors_plumb'}))

        if hand_is_paper(hand):
            if hand_is_rock(other_hand):
                valid_actions.append(Action('special', source=source_index, targets=[1 - source_index], params={'ability': 'paper'}))
            if hand_is_rock(opp_left):
                valid_actions.append(Action('special', source=source_index, targets=[2], params={'ability': 'paper'}))
            if hand_is_rock(opp_right):
                valid_actions.append(Action('special', source=source_index, targets=[3], params={'ability': 'paper'}))

        if hand_is_rock(hand):
            if hand_is_scissors(other_hand):
                valid_actions.append(Action('special', source=source_index, targets=[1 - source_index], params={'ability': 'rock'}))
            if hand_is_scissors(opp_left):
                valid_actions.append(Action('special', source=source_index, targets=[2], params={'ability': 'rock'}))
            if hand_is_scissors(opp_right):
                valid_actions.append(Action('special', source=source_index, targets=[3], params={'ability': 'rock'}))

    return valid_actions


def hand_is_paper(hand):
    return hand.alive and (hand.value == 5 or hand.value == 4) and hand.state == 1

def hand_is_rock(hand):
    return hand.alive and hand.value == 5 and hand.state == 0

def hand_is_scissors(hand):
    return hand.alive and (hand.value == 2 or hand.value == 3 or (hand.value == 4 and hand.state == 0)) 

def hand_is_boinger(hand):
    return hand.alive and hand.value == 1

def hand_requires_state(hand):
    return hand.alive and hand.state >= 2


# encoding
def action_to_id(action):
    return ACTION_TO_ID[action]

# decoding
def id_to_action(action_id):
    return ID_TO_ACTION[action_id]

