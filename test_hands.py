from hands import *

def test_hand_encodings():
    hand = Hand()
    hand.alive = 0
    encoding = hand.encode_state()
    if encoding != 0:
        print('Encoding issue: ', hand)

    for i in range (5):
        val = i + 1
        hand = Hand()
        hand.value = val
        for form in range (2):
            hand.state = form
            encoding = hand.encode_state()

            if val < 4 and encoding != val:
                print('Encoding issue: ', hand)
            elif val == 4:
                if form == 0 and encoding != 4:
                    print('Encoding issue: ', hand)
                if form == 1 and encoding != 5:
                    print('Encoding issue: ', hand)
            elif val == 5:
                if form == 0 and encoding != 6:
                    print('Encoding issue: ', hand)
                if form == 1 and encoding != 7:
                    print('Encoding issue: ', hand)
