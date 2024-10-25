import sys
import time
from socket_manager import SocketManager
from board import Board
from utils import *
from search import Node
from heuristics import black_heuristics, white_heuristics

PORT = {"WHITE":5800, "BLACK":5801}

VERBOSE = True      # quickly enable/disable verbose

# TYPE = "random"                            # quickly choose the type of search
# TYPE = "breadth-first"                     # quickly choose the type of search
# TYPE = "depth-first"                       # quickly choose the type of search
# TYPE = "greedy"                            # quickly choose the type of search
# TYPE = "A*"                                # quickly choose the type of search
TYPE = "A*_alpha_beta_cut"                 # quickly choose the type of search

def main():
    
    ## Check that there aren't missing or excessing args ##
    if len(sys.argv) != 4:
        if VERBOSE : print("Wrong number of args, it should be: python3 __main__.py <color(White/Black)> <timeout(seconds)> <IP_server>")
        sys.exit(1)
    
    ## Check args are corrected ##
    # - Color
    color = sys.argv[1].upper()
    if color not in PORT.keys():
        if VERBOSE : print("Wrong color, it should be \"White\" or \"Black\"")
        sys.exit(1)
        
    # - Timeout
    try:
        timeout = int(sys.argv[2])
    except ValueError:
        if VERBOSE : print("Wrong timeout, it should be an integer")
        sys.exit(1)
    
    # - Ip address + 
    ip = sys.argv[3]          
    if not check_ip(ip):
        if VERBOSE : print("Wrong ip format")
        sys.exit(1)
    port = PORT[color]
    
    ## Initialize the socket ##
    s = SocketManager(ip, port)
    s.create_socket()
    s.connect()
    
    ###############################################################################
    ### GAME CYCLE ################################################################
    ###############################################################################
    
    # May be useful
    boards_history = []     # List of the boards, useful to track the game
    
    try:
        while True:
            initial_time = time.time()
            
            ## 1) Read current state / state updated by the opponent move
            current_state = s.get_state()
            b = Board(state=current_state)
            
            # Memorize opponent move
            boards_history.append(b) 

            # if VERBOSE : print(f"Current table:\n{current_state}")
            if VERBOSE : 
                print(f"Current table:\n")
                b.pretty_print()

            # If we are still playing
            if b.turn == color:
                if VERBOSE : print("It's your turn")

                ## 2) Compute the move
                timeout = timeout - (time.time() - initial_time) # consider initialization time

                heuristic = white_heuristics if color=="WHITE" else black_heuristics
                n = Node(b, h=heuristic)     
                
                match TYPE:
                    case "random" : 
                        _from, _to = n.random_search()
                    case "breadth-first" : 
                        _from, _to = n.breadth_first_search(timeout)
                    case "depth-first" : 
                        _from, _to = n.depth_first_search(timeout)
                    case "greedy" : 
                        _from, _to = n.greedy_best_first_search(timeout)
                    case "A*" : 
                        _from, _to = n.a_star_search(timeout)
                    case "A*_alpha_beta_cut" : 
                        num_opponent_pred = 2
                        _from, _to = n.a_star_with_opponent_prediction(
                                        depth=num_opponent_pred, 
                                        timeout=timeout - num_opponent_pred  # giving less time because time will get 
                                                                             # lost in current-opponent steps
                                    )
                    case _ :
                        raise Exception("Search strategy not implemented yet")
                
                # Translate the move
                _from = tuple2alfanum(_from)
                _to = tuple2alfanum(_to)
                move = (_from, _to, color) 
                if VERBOSE : print(f"Move: {move}")
                
                ## 3) Send the move
                s.send_move(move)
                
                ## 4) Read the new updated state after my move
                current_state = s.get_state()
                b = Board(state=current_state)
                
                # memorize my move
                boards_history.append(b) 
                if VERBOSE : 
                    print(f"After my move:\n")
                    b.pretty_print()
                    
            # Else the game ends for many reasons
            elif current_state['turn'] == "WHITEWIN":
                if VERBOSE : print("WHITE wins!")
                sys.exit(0)
            elif current_state['turn'] == "BLACKWIN":
                if VERBOSE : print("BLACK wins!")
                sys.exit(0)
            elif current_state['turn'] == "DRAW":
                if VERBOSE : print("It's a draw!")
                sys.exit(0)
            else:
                if VERBOSE : print("Waiting for your opponent move...")

    except Exception as e:
        if VERBOSE : print(f"An error occurred during the game: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()