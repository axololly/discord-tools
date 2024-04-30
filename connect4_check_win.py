class Connect4_CheckWins:
    ...
    def check_win(self):
        # rotate the board for checking columns easier
        rotated_board = [
            [
                self.board[-1 - i][x] for i, _ in enumerate(self.board)
            ]
            for x, _ in enumerate(self.board[0])
        ]

        # vertical and horizontal
        for board in [self.board, rotated_board]:
            for row in board:
                for i in range(4):
                    line = row[i : i + 4]
                    
                    if len(set(line)) == 1 and 0 not in line:
                        return line[0]

        # diagonals
        for x_change in (1, -1):
            for i in range(3):
                for j in range(4):
                    line = [self.board[i + x][j + x * x_change] for x in range(4)]
                    
                    if len(set(line)) == 1 and 0 not in line:
                        return line[0]
                    
        if not self.valid_moves():
            return 0
        
        return False
