import discord, random
from datetime import datetime as dt, timedelta as td
from discord import app_commands, ui, Interaction, ButtonStyle as BS
from discord.ext import commands
from _requestplayview import RequestToPlayView

class ColumnIsFullError:
    pass

class Board:
    def __init__(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)] # Initialise a board full of zeroes

    def place_counter(self, column, player):
        # This places a counter on the top layer of the board.
        self.board[0][column - 1] = player
        # This compresses the board to move it down.
        self.compress()
        
        # If the column is full, return an error for the button to disable itself.
        # This means no more counters can be placed there again.
        if self.board[0][column - 1] != 0:
            return ColumnIsFullError
    
    def compress(self):
        # This moves everything on the board as far as it can go.
        # It checks each board cell to see if it has a piece and then if that piece has space below it, it moves it down.

        # First copy the board to not affect anything currently.
        state = self.board

        for c, line in enumerate(state): # Search each line
            for count, item in enumerate(line): # Search each cell in that line
                if item != 0: # If the space is a piece and not a gap
                    if c + 1 <= len(state) - 1: # If this is not the bottom (where you can't go further)
                        if state[c + 1][count] == 0: # If the space underneath the piece is a gap
                            # Swap the piece to the space underneath
                            state[c + 1][count] = item
                            state[c][count] = 0
        
        self.board = state # Update the board to reflect the changes.

    def read_lines(self, state):
        for board_line in state: # For every line on the given state
            repeats = 1 # The number of times a given piece has been seen in a line
            item = None

            for iterable in board_line: # For every space on the given line
                if iterable == 0: # If the space is a 0, reset the repeats count because the line is disrupted
                    repeats = 1
                    continue
                
                if iterable == item: # If we see the item again, we know it's repeated
                    repeats += 1
                elif not item:
                    pass # If the item hasn't been assigned yet, just carry on. We assign it later automically.
                else:
                    repeats = 1 # Reset the repeats because another piece that's not the item we're watching has been found; another piece disrupted the line.
                    
                item = iterable # Set the item we're looking for to the space we're looking at

                if repeats == 4: # If we find a line of 4
                    if item == 1:
                        return 1 # Return Player 1 won
                    if item == 2:
                        return 2 # Return Player 2 won
    
                        
    def rotate_90(self, matrix): # rotate 90 degrees clockwize
        return [[matrix[-1-i][x] for i, _ in enumerate(matrix)] for x, _ in enumerate(matrix)]
    
    def horizontalflip(self, matrix): # flips along x axis
        return [line[::-1] for line in matrix]

    def get_new(self, x, y): # needed for rotate_45()
        if x + 1 > -1 and y - 1 > -1:
            return (x + 1, y - 1)

    def rotate_45(self, matrix): # rotate 45 degrees clockwise
        matrix_coords = [[(x, y) for x, _ in enumerate(line)] for y, line in enumerate(matrix)]

        last_row = matrix_coords[-1]
        first_col = [matrix_coords[i][0] for i, _ in enumerate(matrix_coords)]

        diag_starts = first_col + last_row[1:]
        diagonals = []
        
        for diagonal in diag_starts:
            x, y = diagonal
            D = []

            while self.get_new(x, y):
                try:
                    f = matrix_coords[y][x]
                except IndexError:
                    break
                else:
                    D.append((x, y))
                    x, y = self.get_new(x, y)

            D.append((x, y))
            
            diagonals.append(D)

        for d in diagonals:
            for c, v in enumerate(d):
                if v[0] == len(last_row):
                    del d[c]
                else:
                    x, y = v
                    d[c] = matrix[y][x]
        
        for i, d in enumerate(diagonals):
            if not d:
                del diagonals[i]
        
        return diagonals
    
    def check(self):
        wins = [
            self.read_lines(self.board), # Read horizontal lines
            self.read_lines(self.rotate_90(self.board)), # Read vertical lines
            self.read_lines(self.rotate_45(self.board)), # Read one set of diagonal lines
            self.read_lines(self.rotate_45(self.horizontalflip(self.board))) # Read the other set of diagonal lines
        ]

        if 1 in wins:
            return 1 # If player 1 gets a Connect 4, return Player 1 won
        if 2 in wins:
            return 2 # If player 2 gets a Connect 4, return Player 2 won
        
        zeroes = 0
        for line in self.board:
            zeroes += line.count(0)
        
        if zeroes == 0:
            return False # If the board is full with pieces and no winner, return a draw

class ColumnsButton(ui.Button):
    def __init__(self, column):
        super().__init__(
            label = column,
            style = BS.blurple,
            row = column // 5
        )
        self.column = column # Get a number from 1 to 7
    
    async def callback(self, interaction: Interaction):
        if interaction.user == self.view.players[self.view.player]:
            A = self.view.play_move(self.column)
            await self.view.play(A, interaction, self)
        else:
            await interaction.response.send_message(content = "it's not your turn.", ephemeral = True)

class Columns(ui.View):
    def __init__(self, *players, bet: int = 0):
        super().__init__()
        self.board = Board()

        cancel_button = self.children[0]
        self.remove_item(cancel_button)

        for i in range(7):
            self.add_item(ColumnsButton(i + 1, row = i % 5))
        
        self.add_item(cancel_button)

        random.shuffle(players)
        self.player = random.choice([1, 2])
        self.coin = ['🔴', '🟡'][self.player - 1]
        self.players = {n + 1: players[n] for n, _ in enumerate(players)}

        self.bet = bet
        self.timeout = 30
        self.cancelled = True
        self.cancel_user = self.players[self.player]

    async def on_callback(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        self.cancelled = True
        self.cancel_user = self.players[self.player]
        await self.on_callback()
        self.stop()

    def play_move(self, column):
        if self.board.place_counter(column, self.player) is ColumnIsFullError: # Place the counter and check if it returns that column error
            return -1
        
        winner = self.board.check() # Check if anybody has won yet

        if winner:
            return winner # Return who won (either Player 1 or Player 2)
        elif winner is False:
            return 0 # There's a draw
        
        self.player = 2 if self.player == 1 else 1

    def retrieve_board(self): # Write out the board
        board_str = f":one::two::three::four::five::six::seven:\n" # Headers (to show the columns that relate to the buttons)
        board_str += "\n".join(["".join([str(i) for i in self.board.board[x]]) for x, _ in enumerate(self.board.board)]) # The board itself
        
        # Relace 0s with black squares, 1s with red counters and 2s with yellow counters
        board_str = board_str.replace('0', '⬛').replace('1', '🔴').replace('2', '🟡')
        return board_str
    
    async def play(self, A, interaction, button):
        if A == -1: # If the column is full
            button.disabled = True # Disable the button
            await interaction.response.edit_message(view = self) # Update the view
        
        elif A == 0: # If it's a draw
            await interaction.response.edit_message(embed = self.draw_embed, view = None) # Update with the draw_embed
            self.stop() # Stop listening for input
        
        elif A in [1, 2]:
            self.cancelled = False # Show nobody ran away
            await self.on_callback() # Disable all buttons
            self.stop() # Stop listening for input
        
        else:
            if self.player == 1: # If it's player 1, use the red counter
                self.coin = "🔴"
                embedcolour = discord.Color.red() # Change the embed to red
            else:
                self.coin = "🟡"
                embedcolour = 0xfdfd96 # Change the embed to yellow

            await interaction.response.edit_message(
                    content = self.players[self.player].mention, # Ping the person playing
                    view = self, # Update the view
                    embed = discord.Embed(
                        title = f"{self.coin} Connect 4", # Show who's turn it is
                        description = self.retrieve_board(), # Get the formatted board state
                        color = embedcolour # Change the embed colour
                    )
                )
    
    @ui.button(label = "❌", style = BS.red, row = 1)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        if not interaction.user in self.players.values():
            await interaction.response.send_message(content = "you're not involved, lil bro", ephemeral = True)
            return
        
        self.cancel = True # Show someone cancelled the match

        self.coin = "🔴" if self.player == 1 else "🟡" # Change to red if it's Player 1, yellow if it's player 2

        await self.on_timeout() # Update the cancel_user to the user that cancelled the match
        self.stop() # Stop listening for input


class Connect4(commands.Cog):
    game = app_commands.Group(name = 'game', description = "Play games.")

    @app_commands.command(name = "connect4", description = "Play Connect 4 with another user. Have fun!")
    @commands.cooldown(1, 30, commands.BucketType.user) # Set a 30s cooldown after playing
    async def connect4(self, interaction: Interaction, opponent: discord.Member = None):
        if not opponent or opponent == interaction.user: # If theres no opponent or the opponent is the user running the command
            await interaction.response.send_message(
                ephemeral = True,
                embed = discord.Embed(
                    description = "You can't play with yourself. Go touch grass and find some new friends! :park:",
                    color = discord.Color.red()
                )
            )
            return

        if opponent == self.bot: # If the opponent is this bot
            await interaction.response.send_message("You can't play with me at the moment. I'm busy. :x:")
            return
            
        view = RequestToPlayView(interaction.user, opponent, game = "Connect 4")

        requestToPlay = discord.Embed(
            title = ":mag: Someone wants to play a game of Connect 4!",
            description = f"{opponent.mention}, do you want to play Connect 4 with {interaction.user.mention}?",
            color = discord.Color.dark_embed()
        )
        await interaction.response.send_message(content = opponent.mention, embed = requestToPlay, view = view) # Ask to play

        view.message = await interaction.original_response() # Get the message sent above
        
        await view.wait() # Wait for a response

        if not view.value: # If there's no response, exit the command
            return
        
        await view.message.delete() # Delete the request to play message

        game_view = Columns(interaction.user, opponent) # Setup the game view
        
        # Setup the game message
        board_message = await interaction.response.send_message(
            content = game_view.players[game_view.player].mention,
            embed = discord.Embed(
                title = "**Connect 4**",
                description = game_view.retrieve_board(),
                color = discord.Color.blurple()
            ), view = game_view
        )

        await game_view.wait() # Play the game

        # Announce who the winner is
        if not game_view.cancelled: # If the game HASN'T been cancelled
            await board_message.edit(
                content = None,
                embed = discord.Embed(
                    title = "🏆 Connect 4",
                    description = game_view.retrieve_board() + f"\n\nLooks like {game_view.players[game_view.player].mention} won the game! Well done!",
                    color = discord.Color.green()
                ), view = None
            )
        else: # If the game HAS been cancelled
            players = list(game_view.values())
            # This basically checks for the user that's NOT the winner and then finds it in a list of the two players
            winner = [p for p in players if p != game_view.cancel_user][0]

            # Announce the person who ran away and say who won
            await board_message.edit(
                content = game_view.players[game_view.player].mention, view = None, embed = discord.Embed(
                    title = f"{game_view.coin} Connect 4",
                    description = game_view.retrieve_board() + f"\n\n💸 {game_view.cancel_user.mention} ran from the match, which means {winner.mention} won the match!",
                    color = 0xf8c8dc
                )
            )
    
    @connect4.error
    async def connect4_errors(self, ctx, error):
        if isinstance(error, commands.errors.CommandOnCooldown): # If the error is due to a cooldown
            await ctx.reply(
                embed = discord.Embed(
                    title = "Slow down!",
                    description = f"You can play this game again {discord.utils.format_dt(dt.now() + td(seconds = error.retry_after))}",
                    color = discord.Color.red()
                )
            )
        else:
            raise error

async def setup(bot):
  await bot.add_cog(Connect4(bot))
