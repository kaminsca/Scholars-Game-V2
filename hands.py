
class Hand: 
    # value: range from 1-5
    # state: range from 0-3 (0/1 are scissors/paper or rock/paper; 2 is pending -> same player's turn, 3 is pending -> change players)
    # alive: boolean 0 or 1
    def __init__(self):
        self.value = 1
        self.state = 0
        self.alive = 1

    def encode_state(self):
        if self.alive == 0:
            return 0
        elif self.value < 4: 
            return self.value
        elif self.value == 4:
            return 4 + self.state 
        elif self.value == 5:
            return 8 + self.state 
    
    def set_as_encoded_state(self, encoded_state):
        if encoded_state == 0:
            self.alive = 0
        elif encoded_state < 4:
            self.value = encoded_state
            self.alive = 1
            self.state = 0
        elif encoded_state < 7:
            self.value = 4
            self.alive = 1
            self.state = encoded_state - 5
        else:
            self.value = 5
            self.alive = 1
            self.state = encoded_state - 8
    
    def print_hand(self):
        print(f"      living: {self.alive}")
        print(f"      value: {self.value}")
        print(f"      state: {self.state}")