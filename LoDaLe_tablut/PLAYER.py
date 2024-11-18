import sys
import time
from socket_manager import SocketManager
from board import Board
from utils import *
from search import Node
from heuristics import grey_heuristic
import numpy as np
import traceback

PORT = {"WHITE":5800, "BLACK":5801}

H_FLAGS = ["grey", "b/w"]

VERBOSE = True      # quickly enable/disable verbose

TYPE = "search-algorithm" # TODO: rimuovere se non usiamo altro
# TYPE = "machine-learning"
# TYPE = "genetic-algorithm"

SEARCH_TYPE = "alpha_beta_cut"               

def main():
    
    ## Check that there aren't missing or excessing args ##
    if len(sys.argv) != 5:
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
    
    # - Ip address 
    ip = sys.argv[3]          
    if not check_ip(ip):
        if VERBOSE : print("Wrong ip format")
        sys.exit(1)
    port = PORT[color]
    
    # - Heuristic FLAG        # TODO: togliere
    h_flag = sys.argv[4]
    if h_flag not in H_FLAGS:
        if VERBOSE : print(f"Wrong heuristic_flag (must be in {H_FLAGS})")
        sys.exit(1)
    
    ## Initialize the socket ##
    s = SocketManager(ip, port)
    s.create_socket()
    s.connect()
    
    ###############################################################################
    ### GAME CYCLE ################################################################
    ###############################################################################
        
    # Useful vars
    if TYPE == "machine-learning" : 
        dataset_path = "../dataset"
        dataset = np.load(dataset_path + "/dataset_moves.npy", allow_pickle=True)
        results = np.load(dataset_path + "/dataset_results.npy", allow_pickle=True)
        n = 0
    
    try:
        while True:
            initial_time = time.time()
            
            ## 1) Read current state / state updated by the opponent move
            try: current_state = s.get_state()
            except TypeError: pass # if loses can't read
            b = Board(current_state)

            # if VERBOSE : print(f"Current table:\n{current_state}")
            if VERBOSE : 
                print(f"Current table:\n")
                b.pretty_print()

            # If we are still playing
            match current_state["turn"] :
                case  _ if current_state["turn"] == color:
                    if VERBOSE : print("It's your turn")

                    ## 2) Compute the move
                    timeout = timeout - (time.time() - initial_time) # consider initialization time   
                    
                    match TYPE:
                        case "search-algorithm" :
                            n = Node(b)  
                            score, move = n.minimax_alpha_beta(
                                maximizing_player=(color=="WHITE"),
                                h_flag=h_flag,
                                depth=3
                            )
                        case "genetic-algorithm" :
                            move = ...
                            pass
                        case "machine-learning" :
                            idx_moves = 0
                            moves = get_n_most_winning_move(dataset, results, n, color)
                            
                            move = moves[idx_moves][0]
                            from_x, from_y = alfnum2tuple(move[0])
                            to_x, to_y = alfnum2tuple(move[1])
                            
                            while not b.is_valid_move(from_x, from_y, to_x, to_y, b.board[from_x][from_y]) :
                                idx_moves += 1
                                if idx_moves>=len(moves):
                                    move = Node(b).random_search()  # random move if he can't find anything     # TODO: can do better
                                    (from_x, from_y), (to_x, to_y) = move
                                else :
                                    move = moves[idx_moves][0]
                                    from_x, from_y = alfnum2tuple(move[0])
                                    to_x, to_y = alfnum2tuple(move[1])
                                    
                            n += 1
                            
                    # Translate the move
                    _from = tuple2alfanum((from_x, from_y))
                    _to = tuple2alfanum((to_x, to_y))
                    move = (_from, _to, color)
                    
                    if VERBOSE : 
                        print(f"Move: {move}")
                        print(f"{b.board[from_x][from_y]} ({from_x,from_y}) --> {b.board[to_x][to_y]}({to_x,to_y})")
                    
                    ## 3) Send the move
                    s.send_move(move)
                    
                    ## 4) Read the new updated state after my move
                    current_state = s.get_state()
                    
                    # memorize my move
                    if VERBOSE : 
                        print(f"After my move:\n")
                        b.pretty_print()
                        
                case "WHITEWIN":
                    if VERBOSE : print("WHITE wins!")
                    sys.exit(0)
                    
                case "BLACKWIN":
                    if VERBOSE : print("BLACK wins!")
                    sys.exit(0)
                    
                case "DRAW":
                    if VERBOSE : print("It's a draw!")
                    sys.exit(0)
                    
                case _ :
                    if VERBOSE : print("Waiting for your opponent move...")

    except Exception:
        if VERBOSE : print(f"An error occurred during the game:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()