from hands import *

class Player:
    def __init__(self):
        self.left = Hand()
        self.right = Hand()

    def get_hands(self):
        return [self.left, self.right]

    def encode_state(self):
        return [hand.encode_state() for hand in self.get_hands()]
    
    def apply_encoded_state(self, encoded_state):
        self.left.set_as_encoded_state(encoded_state[0])
        self.right.set_as_encoded_state(encoded_state[1])

    def print_player(self):
        print('   left: ')
        self.left.print_hand()
        print('   right: ')
        self.right.print_hand()


    def is_alive(self):
        return any(hand.alive for hand in self.get_hands())
