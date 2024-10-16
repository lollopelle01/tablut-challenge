import sys
import numpy as np
import time
from network.socket_manager import SocketManager
from utils import check_ip, check_timeout

PORT = {"white":5800, "black":5801}
V = True # in order to quickly enable or disable verbose

def main():
    ## Check that there aren't missing or excessing args ##
    if len(sys.argv) != 4:
        if V : print("Wrong number of args, it should be: python3 __main__.py <color(White/Black)> <timeout(seconds)> <IP_server>")
        sys.exit(1)
    
    ## Check args are corrected ##
    # - Color
    color = sys.argv[1].lower()
    if color!="white" and color!="black":
        if V : print("Wrong color, it should be \"White\" or \"Black\"")
        sys.exit(1)
        
    # - Timeout
    try:
        timeout = int(sys.argv[2])
    except ValueError:
        if V : print("Wrong timeout, it should be an integer")
        sys.exit(1)
    
    # - Ip address + 
    ip = sys.argv[3]          
    if not check_ip(ip):
        if V : print("Wrong ip format")
        sys.exit(1)
    port = PORT[color]
    
    ## Initialize the socket ##
    s = SocketManager(ip, port)
    s.create_socket()
    s.connect()
    
    ###############################################################################
    ### GAME CYCLE ################################################################
    ###############################################################################
    
    timeout = time.time() + timeout
    
    # May be useful
    boards_history = []     # List of the boards, useful to track the game
    
    try:
        while True:
            # 1) Read current state / state updated by the opponent move
            current_state = s.get_state()
            boards_history.append(current_state['board']) # memorize opponent move
            check_timeout(timeout)
            
            if V : print(f"Current state:\n{current_state}")

            # If we are still playing
            if current_state['turn'] == color:
                if V : print("It's your turn")

                # 2) Compute the move
                # AI stuff in order to compute _from and _to
                _from = ...
                _to = ...
                move = (_from, _to, color) 
                check_timeout(timeout)
                
                # 3) Send the move
                s.send_move(move)
                check_timeout(timeout)
                
                # 4) Read the new updated state after my move
                current_state = s.get_state()
                boards_history.append(current_state['board']) # memorize my move
                check_timeout(timeout)
                    
            # Else the game ends for many reasons
            elif current_state['turn'] == "WHITEWIN":
                if V : print("WHITE wins!")
                sys.exit(0)
            elif current_state['turn'] == "BLACKWIN":
                if V : print("BLACK wins!")
                sys.exit(0)
            elif current_state['turn'] == "DRAW":
                if V : print("It's a draw!")
                sys.exit(0)
            else:
                if V : print("Waiting for your opponent move...")

    except Exception as e:
        if V : print(f"An error occurred during the game: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()