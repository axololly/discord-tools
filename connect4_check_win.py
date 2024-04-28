class Connect4_CheckWins:
    ...
    def is_game_over(self):
        rotated_board = [
            [
                self.board[-1 - i][x] for i, _ in enumerate(self.board[0])
            ]
            for x, _ in enumerate(self.board)
        ]

        for board in [self.board, rotated_board]:
            for row in board:
                for i in range(4):
                    if all(row[i:i + 4]) in (1, 2):
                        return all(row[i:i + 4])

        # diagonals
        for x_change in (1, -1):
            for i in range(3):
                for j in range(4):
                    if all([self.board[i + x][j + x * x_change] for x in range(4)]) in (1, 2):
                        return all([self.board[i + x][j + x * x_change] for x in range(4)])  
                    
        if self.board[0].count(0) == 0:
            return 0
        
        return False
