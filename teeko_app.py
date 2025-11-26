import streamlit as st
import random

class TeekoPlayer:
    """ An object representation for an AI game player for the game Teeko.
    """
    board = [[' ' for j in range(5)] for i in range(5)]
    pieces = ['b', 'r']

    def __init__(self):
        """ Initializes a TeekoPlayer object by randomly selecting red or black as its
        piece color.
        """
        #self.my_piece = random.choice(self.pieces)
        #self.opp = self.pieces[0] if self.my_piece == self.pieces[1] else self.pieces[1]
        self.my_piece = 'r'
        self.opp = 'b'

    # p = 1 if max player, p = -1 if min player
    def succ(self, state, p, return_move = False):
        my_piece = self.my_piece if p == 1 else self.opp
        successors = []
        
        # Determine if it is drop phase
        number_of_markers = 0
        for row in state:
            for element in row:
                if element != ' ':
                    number_of_markers += 1

        drop_phase = number_of_markers < 8

        if drop_phase:
            for i in range(5):
                for j in range(5):
                    if state[i][j] == ' ':
                        next = [row[:] for row in state] # Making deep copy
                        next[i][j] = my_piece
                        if not return_move:
                            successors.append(next)
                        else:
                            successors.append(( next, (i,j), 0))
        else:
           possible_moves = [(-1, -1), (-1, 0), (-1, 1),
                            (0, -1),            (0, 1),
                            (1, -1), (1, 0), (1, 1)]
           for i in range(5):
                for j in range(5):
                    if state[i][j] == my_piece:
                        for x, y in possible_moves:
                            new_x = i+x
                            new_y = j+y
                            if (0 <= new_x < 5 and 0 <= new_y < 5) and state[new_x][new_y] == ' ':
                                next = [row[:] for row in state] # Making deep copy
                                next[new_x][new_y] = my_piece
                                next[i][j] = ' '
                                if not return_move:
                                    successors.append(next)
                                else:
                                    successors.append(( next, (new_x, new_y), (i,j)))
        return successors

    # p = 1 if max player, p = -1 if min player
    # Count the number of max connected pieces
    def count(self, state, i, j, p):
        my_piece = self.my_piece if p == 1 else self.opp
        # For each relevant piece, we only need check right, down, left-down diagonal, right-down diagonal to ...
        # ... avoid redundancies.
        directions = [(0, 1), (1, 0), (1, -1),  (1, 1)]
        max_count = 0
        for di, dj in directions:
            count = 1
            nexti = i + di
            nextj = j + dj
            max_current_count = 0

            while (0 <= nexti < 5 and 0 <= nextj < 5):
                count = count + 1 if state[nexti][nextj] == my_piece else 0
                max_current_count = max(max_current_count, count)                    
                nexti += di
                nextj += dj

            max_count = max(max_count, max_current_count)

        # Now checking for squares pattern:
        # For each point, only have to check the right, down and down-right diagonal adjacent neigbors, ...
        # ... the number of connected pieces is just the number of the pieces in the square pattern.
        directions = [(0,1), (1,0), (1,1)]
        count = 1
        for di, dj in directions:
            nexti = i + di
            nextj = j + dj
            if (0 <= nexti < 5 and 0 <= nextj < 5) and state[nexti][nextj] == my_piece:
                count += 1

        max_count = max(max_count, count)
        return max_count

    # p = 1 if max player, p = -1 if min player
    def heuristic_game_value(self, state, p):
        score = self.game_value(state)
        if score == 0:
            for i in range(5):
                for j in range(5):
                    if p == 1 and state[i][j] == self.my_piece:
                        score = max(score, self.count(state, i, j, p))
                    elif p == -1 and state[i][j] == self.opp:
                        score = min(score, -self.count(state, i, j, p))
            score = score / 4 * p 

        return score

    # p = 1 if max player, p = -1 if min player
    def minimax_value(self, state, depth, p, alpha, beta):
        h = self.heuristic_game_value(state, p)
        if abs(h) == 1 or depth > 3: 
            return h

        successors = self.succ(state, p)
        if p == 1:
            for succ in successors:
                alpha = max(alpha , self.minimax_value(succ, depth+1, -p, alpha, beta))
                if alpha >= beta: 
                    break
            return alpha
        else:
            for succ in successors:
                beta = min(beta, self.minimax_value(succ, depth+1, -p, alpha, beta))
                if alpha >= beta: 
                    break
            return beta
    

    def best_response(self, state):
        successors = self.succ(state, 1, True) # a list of tuples (next_state, move coordinate, origin coordinate)
        best_move = []
        v = -2

        for succ_state, move_coor, origin_coor in successors:
            current = self.minimax_value(succ_state, 0, -1, -float('inf'), float('inf'))
            if current > v:
                v = current
                best_move = [move_coor, origin_coor]

        # if origin_coor is 0 and not a tuple, then this is the best_response during drop phase
        return [best_move[0]] if origin_coor == 0 else best_move

    def make_move(self, state):
        """ Selects a (row, col) space for the next move. You may assume that whenever
        this function is called, it is this player's turn to move.

        Args:
            state (list of lists): should be the current state of the game as saved in
                this TeekoPlayer object. Note that this is NOT assumed to be a copy of
                the game state and should NOT be modified within this method (use
                place_piece() instead). Any modifications (e.g. to generate successors)
                should be done on a deep copy of the state.

                In the "drop phase", the state will contain less than 8 elements which
                are not ' ' (a single space character).

        Return:
            move (list): a list of move tuples such that its format is
                    [(row, col), (source_row, source_col)]
                where the (row, col) tuple is the location to place a piece and the
                optional (source_row, source_col) tuple contains the location of the
                piece the AI plans to relocate (for moves after the drop phase). In
                the drop phase, this list should contain ONLY THE FIRST tuple.

        Note that without drop phase behavior, the AI will just keep placing new markers
            and will eventually take over the board. This is not a valid strategy and
            will earn you no points.
        """
        # print(self.minimax_value([[' ', 'b', ' ', 'b', 'b'],
        #     [' ', ' ', 'r', ' ', ' '],
        #     [' ', ' ', 'r', ' ', ' '],
        #     [' ', ' ', ' ', 'r', ' '],
        #     [' ', ' ', ' ', ' ', ' ']], 0, 1))

        # print(self.minimax_value([['b', 'r', 'r', 'r', ' '], ['b', ' ', ' ', ' ', ' '], ['b', ' ', ' ', ' ', ' '], 
        # [' ', ' ', ' ', ' ', ' '], [' ', ' ', ' ', ' ', ' ']], 0, -1, -float('inf'), float('inf')))

        # print(self.best_response([['b', 'r', 'r', 'r', ' '], ['b', ' ', ' ', ' ', ' '], ['b', ' ', ' ', ' ', ' '], 
        #     [' ', ' ', ' ', ' ', ' '], [' ', ' ', ' ', ' ', ' ']]))
        # print(self.best_response([['b', 'b', 'r', ' ', ' '], [' ', ' ', ' ', ' ', ' '],
        #                         [' ', ' ', ' ', ' ', ' '], [' ', 'r', ' ', ' ', ' '],
        #                         [' ', ' ', ' ', ' ', ' ']]))

        # ensure the destination (row,col) tuple is at the beginning of the move list
        return self.best_response(state)

    def opponent_move(self, move):
        """ Validates the opponent's next move against the internal board representation.
        You don't need to touch this code.

        Args:
            move (list): a list of move tuples such that its format is
                    [(row, col), (source_row, source_col)]
                where the (row, col) tuple is the location to place a piece and the
                optional (source_row, source_col) tuple contains the location of the
                piece the AI plans to relocate (for moves after the drop phase). In
                the drop phase, this list should contain ONLY THE FIRST tuple.
        """
        # validate input
        if len(move) > 1:
            source_row = move[1][0]
            source_col = move[1][1]
            if source_row != None and self.board[source_row][source_col] != self.opp:
                self.print_board()
                print(move)
                raise Exception("You don't have a piece there!")
            if abs(source_row - move[0][0]) > 1 or abs(source_col - move[0][1]) > 1:
                self.print_board()
                print(move)
                raise Exception('Illegal move: Can only move to an adjacent space')
        if self.board[move[0][0]][move[0][1]] != ' ':
            raise Exception("Illegal move detected")
        # make move
        self.place_piece(move, self.opp)

    def place_piece(self, move, piece):
        """ Modifies the board representation using the specified move and piece

        Args:
            move (list): a list of move tuples such that its format is
                    [(row, col), (source_row, source_col)]
                where the (row, col) tuple is the location to place a piece and the
                optional (source_row, source_col) tuple contains the location of the
                piece the AI plans to relocate (for moves after the drop phase). In
                the drop phase, this list should contain ONLY THE FIRST tuple.

                This argument is assumed to have been validated before this method
                is called.
            piece (str): the piece ('b' or 'r') to place on the board
        """
        if len(move) > 1:
            self.board[move[1][0]][move[1][1]] = ' '
        self.board[move[0][0]][move[0][1]] = piece

    def print_board(self):
        """ Formatted printing for the board """
        for row in range(len(self.board)):
            line = str(row)+": "
            for cell in self.board[row]:
                line += cell + " "
            print(line)
        print("   A B C D E")

    def game_value(self, state):
        """ Checks the current board status for a win condition

        Args:
        state (list of lists): either the current state of the game as saved in
            this TeekoPlayer object, or a generated successor state.

        Returns:
            int: 1 if this TeekoPlayer wins, -1 if the opponent wins, 0 if no winner
        """
        # check horizontal wins
        for row in state:
            for i in range(2):
                if row[i] != ' ' and row[i] == row[i+1] == row[i+2] == row[i+3]:
                    return 1 if row[i]==self.my_piece else -1

        # check vertical wins
        for col in range(5):
            for i in range(2):
                if state[i][col] != ' ' and state[i][col] == state[i+1][col] == state[i+2][col] == state[i+3][col]:
                    return 1 if state[i][col]==self.my_piece else -1

        # check \ diagonal wins 
        starting_points = [(0, 1), (1, 0), (0,0)]
        for x, y in starting_points:
            for i in range(2):
                x += i
                y += i
                if state[x][y] != ' ' and state[x][y] == state[x+1][y+1] == state[x+2][y+2] == state[x+3][y+3]:
                    return 1 if state[x][y] == self.my_piece else -1
                if not x == y == 0: 
                    break

        # check / diagonal wins
        starting_points = [(3, 0), (4, 0), (4,1)]
        for x, y in starting_points:
            for i in range(2):
                x -= i
                y += i
                if state[x][y] != ' ' and state[x][y] == state[x-1][y+1] == state[x-2][y+2] == state[x-3][y+3]:
                    return 1 if state[x][y] == self.my_piece else -1
                if not (x == 4 and y == 0): 
                    break

        # check box wins
        for down in range(4):
            for right in range(4):
                if state[down][right] != ' ' and state[down][right] == state[down + 1][right] == state[down][right + 1] == state[down + 1][right + 1]:
                    return 1 if state[down][right] == self.my_piece else -1

        return 0 # no winner yet

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = [[' ' for j in range(5)] for i in range(5)]
    st.session_state.ai = TeekoPlayer()
    st.session_state.piece_count = 0
    st.session_state.selected_pos = None
    st.session_state.game_over = False
    st.session_state.winner = None

# Page config
st.set_page_config(page_title="Teeko Game", page_icon="🎮", layout="centered")

st.title("🎮 Teeko Game")
st.markdown("**You are Black (●)** | **AI is Red (●)**")

# Game info
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    phase = "Drop Phase" if st.session_state.piece_count < 8 else "Move Phase"
    st.info(f"**Phase:** {phase}")
with col2:
    st.info(f"**Pieces:** {st.session_state.piece_count}/8")
with col3:
    if st.button("🔄 New Game"):
        st.session_state.board = [[' ' for j in range(5)] for i in range(5)]
        st.session_state.piece_count = 0
        st.session_state.selected_pos = None
        st.session_state.game_over = False
        st.session_state.winner = None
        st.rerun()

# Check for winner
def check_winner():
    result = st.session_state.ai.game_value(st.session_state.board)
    if result == 1:
        st.session_state.game_over = True
        st.session_state.winner = "AI"
    elif result == -1:
        st.session_state.game_over = True
        st.session_state.winner = "You"

# Display board
st.markdown("---")
if not st.session_state.game_over:
    if st.session_state.piece_count < 8:
        st.success("**Your turn!** Click an empty square to place your piece.")
    else:
        if st.session_state.selected_pos is None:
            st.success("**Your turn!** Click one of your pieces to select it.")
        else:
            st.warning(f"**Selected:** {chr(st.session_state.selected_pos[1]+65)}{st.session_state.selected_pos[0]} - Click an adjacent empty square to move.")

# CSS for better button styling
st.markdown("""
<style>
    div[data-testid="column"] .stButton > button {
        height: 60px;
        font-size: 28px;
        background-color: #f0f0f0 !important;
        border: 2px solid #333 !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        background-color: #e0e0e0 !important;
        border-color: #000 !important;
    }
    div[data-testid="column"] .stButton > button:active {
        background-color: #f0f0f0 !important;
        box-shadow: none !important;
        transform: none !important;
    }
    div[data-testid="column"] .stButton > button:focus {
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Create board display
cols_header = st.columns([0.5] + [1]*5)
with cols_header[0]:
    st.markdown("")
for idx, letter in enumerate(['A', 'B', 'C', 'D', 'E']):
    with cols_header[idx+1]:
        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{letter}</div>", unsafe_allow_html=True)

for i in range(5):
    cols = st.columns([0.5] + [1]*5)
    with cols[0]:
        st.markdown(f"<div style='text-align: center; font-weight: bold; padding-top: 20px;'>{i}</div>", unsafe_allow_html=True)
    
    for j in range(5):
        with cols[j+1]:
            cell = st.session_state.board[i][j]
            
            # Determine button style and label
            if cell == 'b':
                label = "⚫"
                disabled = st.session_state.game_over or st.session_state.piece_count < 8
            elif cell == 'r':
                label = "🔴"
                disabled = True
            else:
                label = "⬜"
                disabled = st.session_state.game_over
            
            # Handle button click
            if st.button(label, key=f"cell_{i}_{j}", disabled=disabled, use_container_width=True):
                # Drop phase
                if st.session_state.piece_count < 8:
                    if cell == ' ':
                        # Player move
                        st.session_state.board[i][j] = 'b'
                        st.session_state.piece_count += 1
                        check_winner()
                        
                        if not st.session_state.game_over and st.session_state.piece_count < 8:
                            # AI move
                            move = st.session_state.ai.best_response(st.session_state.board)
                            st.session_state.board[move[0][0]][move[0][1]] = 'r'
                            st.session_state.piece_count += 1
                            check_winner()
                        
                        st.rerun()
                
                # Move phase
                else:
                    if cell == 'b' and st.session_state.selected_pos is None:
                        # Select player piece
                        st.session_state.selected_pos = (i, j)
                        st.rerun()
                    elif st.session_state.selected_pos is not None and cell == ' ':
                        # Check if adjacent
                        si, sj = st.session_state.selected_pos
                        if abs(si - i) <= 1 and abs(sj - j) <= 1:
                            # Move player piece
                            st.session_state.board[i][j] = 'b'
                            st.session_state.board[si][sj] = ' '
                            st.session_state.selected_pos = None
                            check_winner()
                            
                            if not st.session_state.game_over:
                                # AI move
                                move = st.session_state.ai.best_response(st.session_state.board)
                                if len(move) > 1:
                                    st.session_state.board[move[0][0]][move[0][1]] = 'r'
                                    st.session_state.board[move[1][0]][move[1][1]] = ' '
                                check_winner()
                            
                            st.rerun()

st.markdown("---")

# Game over message
if st.session_state.game_over:
    if st.session_state.winner == "You":
        st.balloons()
        st.success("🎉 **Congratulations! You won!**")
    else:
        st.error("😔 **AI wins! Better luck next time!**")

# Instructions
with st.expander("📖 How to Play"):
    st.markdown("""
    **Objective:** Get 4 of your pieces in a row (horizontal, vertical, diagonal, or square pattern).
    
    **Drop Phase (First 8 moves):**
    - Click any empty square to place your piece
    - Players alternate placing pieces until all 8 are on the board
    
    **Move Phase:**
    - Click one of your pieces to select it
    - Click an adjacent empty square to move there
    - You can move horizontally, vertically, or diagonally (one square at a time)
    
    **Winning Patterns:**
    - 4 in a row horizontally
    - 4 in a row vertically
    - 4 in a row diagonally
    - 2x2 square formation
    """)

st.markdown("<p style='text-align: center; color: gray;'><i>Developed by Zaaim Syukrin</i></p>", unsafe_allow_html=True)