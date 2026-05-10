from random import choice


from random import choice
#----Variables----
Current_Score = int(0)
Goal_Score = int(0)
row = int(6)
column = int(6)
Item = list(["A", "B", "C", "D", "E", "F"])
board = list([])


#----Creating Board----
def Create_Board():
    """Creates the board[Rows and Columns] of the game"""
    global board

    #----Create Columns and Rows
    for Rows in range(row):
        rws = []

        for Columns in range(column):
            rws.append(choice(Item))

        board.append(rws)

    return board

#----Display Board----
def Display_Board(board_d, goal_score, current_score):
    """Displays the board[Rows and Columns] of the game"""
    print("GOAL: ", goal_score)
    print("Current Goal: ", current_score)
    print()

    for i, display in enumerate(board_d):

        display = ' '.join(display)  # Remove the "" and []
        if i == 0:
            print("   ", 0, 1, 2, 3, 4, 5)
        else:
            print(i, "|", display)



#----Check Column or Row are the same----
def check_for_matches(boards):
    #---Create Empty Set
    matches = set()
    global Current_Score

    #---Check if 3 items are the same in a row
    for rw in range(6):
        for col in range(6-2):
            if boards[rw][col] == boards[rw][col + 1] == boards[rw][col + 2]:#Find the 3 same row points
                Current_Score += 3
                for i in range(3):
                    matches.add((rw,col + i))#Adding the position to an iterable set

            else:
                #---Fall back if code doesn't find any match in a row
                continue



    #---Check if 3 items are the same in a column
    for rw in range(6-2):
        for col in range(6):
            if boards[rw][col] == boards[rw + 1][col] == boards[rw + 2][col]:
                Current_Score += 3
                for i in range(3):
                    matches.add((rw + i ,col))#Adding the position to an iterable set

            else:
                # ---Fall back if code doesn't find any match in a column
                continue


    print(matches)
    return matches

#----Remove found matches----
def Remove_mathces(matches):
    global board

    for rs,cl in matches:
        board [rs][cl] = " "

    #Display_Board(board, Goal_Score, Current_Score)

#----Drop tiles----
def drop_tile(drop_board):
    for clm in range(column):
        empty_spaces = 0
        for rws in range(row-1,-1,-1):
            if drop_board[rws][clm] == " " :
                empty_spaces += 1
            elif empty_spaces > 0:
                drop_board[rws + empty_spaces][clm] = drop_board[rws][clm]
                drop_board[rws][clm] = " "

    #Display_Board(drop_board, Goal_Score, Current_Score)

#---Create new items---
def add_new_item():
    """Adds a new item to the board"""
    global Item

    for Columns in range(column):
        if board[0][Columns] == " ":
                board[0][Columns] = choice(Item)

#----Swaping items----
def Swaping_items():
    # ---Select rows

    swap_posi_rw = input("Select a row: ")
    while swap_posi_rw not in ("0", "1", "2", "3", "4", "5"):
        swap_posi_rw = input("Select a row: ")

    # ---Select column
    swap_posi_col = input("Select a column: ")
    while swap_posi_col not in ("0", "1", "2", "3", "4", "5"):
        swap_posi_col = input("Select a Column: ")

    swap_posi_rw = int(swap_posi_rw)
    swap_posi_col = int(swap_posi_col)

    # ---------

    while True:
        try:
            # ---Asking for move
            switch_posi = input(
                f"selection : {swap_posi_rw, swap_posi_col}\nSelect a move up[U] | down[D] | left[L] | right[R]: : ").upper()

            while switch_posi not in ("U", "D", "L", "R"):
                switch_posi = input(
                    f"Pick item:{swap_posi_rw, swap_posi_col}Select a move up[U] | down[D] | left[L] | right[R]: ").upper()

            # ---------------------------------
            # ---switching down
            if switch_posi == "D":
                old_position = board[swap_posi_rw][swap_posi_col]

                # ---Check if not switching down is correct
                if swap_posi_rw + 1 not in (0, 1, 2, 3, 4, 5):
                    print("Invalid move")
                    continue
                else:  # ---Check if switching down is correct
                    board[swap_posi_rw][swap_posi_col] = board[swap_posi_rw + 1][swap_posi_col]
                    board[swap_posi_rw + 1][swap_posi_col] = old_position
                    #break


            # -------UP--------
            elif switch_posi == "U":  # ---switching Up
                old_position = board[swap_posi_rw][swap_posi_col]

                # ---Check if not switching down is correct
                if swap_posi_rw - 1 not in (0, 1, 2, 3, 4, 5):
                    print("Invalid move")
                    continue
                else:  # ---Check if  switching down is correct
                    board[swap_posi_rw][swap_posi_col] = board[swap_posi_rw - 1][swap_posi_col]
                    board[swap_posi_rw - 1][swap_posi_col] = old_position
                    break

            # -------LEFT--------
            elif switch_posi == "L":  # ---switching Left
                old_position = board[swap_posi_rw][swap_posi_col]

                # ---Check if not switching left is correct
                if swap_posi_col - 1 not in (0, 1, 2, 3, 4, 5):
                    print("Invalid move")
                    continue
                else:  # ---Check if switching left is correct
                    board[swap_posi_rw][swap_posi_col] = board[swap_posi_rw][swap_posi_col - 1]
                    board[swap_posi_rw][swap_posi_col - 1] = old_position
                    break

            # ----RIGHT------
            elif switch_posi == "R":  # ---switching Right
                old_position = board[swap_posi_rw][swap_posi_col]

                # ---Check if not switching right is correct
                if swap_posi_col + 1 not in (0, 1, 2, 3, 4, 5):
                    print("Invalid move")
                    continue
                else:  # ---Check if not switching right is correct
                    board[swap_posi_rw][swap_posi_col] = board[swap_posi_rw][swap_posi_col + 1]
                    board[swap_posi_rw][swap_posi_col + 1] = old_position
                    break
            print("--"*6)
            Display_Board(board, Goal_Score, Current_Score)
        except IndexError:
            print("Invalid input")




Create_Board()
Display_Board(board, Goal_Score, Current_Score)

while True:
    Remove_mathces(check_for_matches(board))
    drop_tile(board)

    while " " in board[0]:
        add_new_item()
        drop_tile(board)

    Display_Board(board, Goal_Score, Current_Score)
    Swaping_items()


    print("_"*80)
    input("Press Enter to Continue...")










