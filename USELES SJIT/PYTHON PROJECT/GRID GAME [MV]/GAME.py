from random import choice

ROWS = 6
COLUMNS = 6
ITEMS = ["A", "B", "C", "D", "E", "F"]


def create_board():
    return [[choice(ITEMS) for _ in range(COLUMNS)] for _ in range(ROWS)]


def display_board(board, goal_score, current_score):
    print(f"GOAL: {goal_score}")
    print(f"Current Score: {current_score}\n")
    print("   ", *range(COLUMNS))
    for i, row in enumerate(board):
        print(i, "|", " ".join(row))
    print()


def check_for_matches(board):
    matches = set()
    score = 0

    # Check rows
    for r in range(ROWS):
        for c in range(COLUMNS - 2):
            if board[r][c] == board[r][c + 1] == board[r][c + 2] != " ":
                for i in range(3):
                    matches.add((r, c + i))
                score += 3

    # Check columns
    for r in range(ROWS - 2):
        for c in range(COLUMNS):
            if board[r][c] == board[r + 1][c] == board[r + 2][c] != " ":
                for i in range(3):
                    matches.add((r + i, c))
                score += 3

    return matches, score


def remove_matches(board, matches):
    for r, c in matches:
        board[r][c] = " "


def drop_tiles(board):
    for c in range(COLUMNS):
        empty = 0
        for r in range(ROWS - 1, -1, -1):
            if board[r][c] == " ":
                empty += 1
            elif empty:
                board[r + empty][c] = board[r][c]
                board[r][c] = " "


def refill_board(board):
    for c in range(COLUMNS):
        if board[0][c] == " ":
            board[0][c] = choice(ITEMS)


def get_position(prompt):
    while True:
        value = input(prompt)
        if value.isdigit() and 0 <= int(value) < ROWS:
            return int(value)


def swap_items(board):
    r = get_position("Select a row: ")
    c = get_position("Select a column: ")

    directions = {
        "U": (-1, 0),
        "D": (1, 0),
        "L": (0, -1),
        "R": (0, 1),
    }

    while True:
        move = input("Move [U/D/L/R]: ").upper()
        if move in directions:
            dr, dc = directions[move]
            nr, nc = r + dr, c + dc

            if 0 <= nr < ROWS and 0 <= nc < COLUMNS:
                board[r][c], board[nr][nc] = board[nr][nc], board[r][c]
                return
            else:
                print("Invalid move.")


# ---------- GAME LOOP ----------

board = create_board()
goal_score = 100
current_score = 0

while True:
    display_board(board, goal_score, current_score)

    matches, gained = check_for_matches(board)
    if matches:
        current_score += gained
        remove_matches(board, matches)
        drop_tiles(board)

        while " " in board[0]:
            refill_board(board)
            drop_tiles(board)
    else:
        swap_items(board)

    if current_score >= goal_score:
        print("🎉 You win!")
        break
