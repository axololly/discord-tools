import discord, random
from discord import app_commands, ui, Interaction, ButtonStyle as BS
from discord.ext import commands
from datetime import datetime as dt, timedelta as td
from math import ceil
from _requestplayview import RequestToPlayView

class TicTacToeButton(ui.Button):
    def __init__(self, ID):
        super().__init__(
            label = "\u200b",
            style = BS.blurple,
            row = ceil(ID / 3) - 1 # Aligh the buttons
        ) 
        self.ID = ID
        
    async def callback(self, interaction: Interaction): # When the button gets clicked
        await self.view.input_move(interaction, self, self.ID) # Input the move

class TicTacToeView(ui.View):
    def __init__(self, *players):
        super().__init__(timeout = 20) # Set the timeout
        [self.add_item(TicTacToeButton(i + 1)) for i in range(9)] # Add the buttons to the view
        self.pieces = {1: 'X', 2: 'O'} # Assign the pieces
        self.board = [[0 for _ in range(3)] for _ in range(3)] # Create the board
        self.players = [None] + players # buffer to use L[x] instead of L[x - 1]
        self.turn = random.randint(1, 2) # Randomly choose a player

    async def on_callback(self):
        for child in self.children:
            child.disabled = True

    async def on_timeout(self):
        # Get the person who's NOT playing now (the person playing now has run away from the game)
        winner = [p for p in self.players if p and p != self.players[self.turn]][0]
        await self.on_callback() # Disable all buttons

        # Update the message
        await self.message.edit(
            content = None,
            embed = discord.Embed(
                title = "⏰  **Timed out!**",
                description = f"Looks like {self.players[self.turn].mention} ran from the game, which means{winner.mention} won!",
                color = discord.Color.red()
            ), view = self
        )

    def rotate_90(self, matrix): # rotate 90 degrees clockwize
        return [[matrix[-1-i][x] for i, _ in enumerate(matrix)] for x, _ in enumerate(matrix)]
    
    def check_for_wins(self):
        lines = [
            [sum(line) for line in self.board], # Check horizontally for a win
            [sum(line) for line in self.rotate_90(self.board)], # Check vertically for a win by rotating the board
            [
                sum(self.board[x][x] for x in range(3)), # Check the up-right diagonal
                sum(self.board[2-x][x] for x in range(3)) # Check the down-right diagonal
            ]
        ]

        for line in lines:
            if 3 in line: # If there's 1, 1, 1, that totals to 3, meaning player 1 has won
                return 1
            elif -3 in line: # If there's -1, -1, -1, that totals to -3, meaning player 2 has won
                return 2
            
            if sum([line.count(0) for line in self.board]) == 1: # If the board is full and nobody has won
                return 0
    
    async def game_end_embed(self, result = None):
        if not result or result != 0: # If there is no result (win, lose, draw), just leave
            return

        if result == 0: # If it's a draw
            header = "Draw!"
            desc = "To be fair, it is just a 3x3 grid."
            colour = 0xc3b1e1
                
        elif result in [1, 2]: # If there is a winner
            header = "🏆 Winner!"
            desc = f"{self.players[result].mention} won as :{self.pieces[result].lower()}:\n(Looks like someone needs to step up their game.)",
            colour = discord.Color.yellow()
        
        # Create the end screen embed
        embed = discord.Embed(
            title = header,
            description = desc[0],
            color = colour
        )

        return embed
        
    async def input_move(self, interaction: Interaction, button: discord.Button, position: int):
        piece_display = {
            'X': '❌',
            'O': '⭕'
        }
        
        if interaction.user == self.players[self.turn]:
            button.label = piece_display[self.pieces[self.turn]]
            button.disabled = True

            if self.pieces[self.turn] == 'X':
                piece_to_place = 1
            if self.pieces[self.turn] == 'O':
                piece_to_place = -1

            x, y = divmod(position, 3)
            
            cells = [
                (0, 0), (0, 1), (0, 2),
                (1, 0), (1, 1), (1, 2),
                (2, 0), (2, 1), (2, 2)
            ]

            x, y = cells[position - 1]
            self.board[x][y] = piece_to_place
            
            if self.turn == 1:
                self.turn = 2
            else:
                self.turn = 1

            E = await self.game_end_embed(self.check_for_wins())
            if E:
                await self.on_callback()
                await interaction.response.edit_message(
                    content = None,
                    embed = E, view = self
                )
                self.stop()
            else:
                await interaction.response.edit_message(
                    content = self.players[self.turn].mention,
                    embed = None, view = self
                )

class TicTacToe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name = "tictactoe", description = "Play tic-tac-toe with another user. Have fun!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def tictactoe(self, interaction: Interaction, opponent: discord.Member = None):        
        if not opponent or opponent == interaction.user: # If the opponent is the person running the command or is None
            await interaction.response.send_message("You can't play with yourself. Go touch grass and find some new friends! :park:")
            return
        
        if opponent == self.bot: # If the opponent is the bot
            await interaction.response.send_message("my maker didn't give me arms to play  :x:")
            return
        
        intro_view = RequestToPlayView(interaction.user, opponent, game = "Tic-Tac-Toe") # Setup the intro view
        
        requestToPlay = discord.Embed(
            title = ":mag: Someone wants to play a game of Tic-Tac-Toe!",
            description = f"{opponent.mention}, do you want to take up the challenge?",
            color = 0xbffcc6
        )
        
        await interaction.response.send_message(embed = requestToPlay, view = intro_view) # Ask the other person if they want to play
        intro_view.message = await interaction.original_response() # Get the message from the above interaction
        await intro_view.wait() # Wait for a response

        if not intro_view.value: # If the person didn't agree, exit the command
            return
        
        await intro_view.message.delete() # Delete the intro message

        game_view = TicTacToeView(interaction.user, opponent) # Setup the game view

        await interaction.followup.send(content = game_view.players[game_view.turn].mention, view = game_view) # Send the game
        game_view.message = await interaction.original_response() # Get the message from the above interaction
        # No need for .wait() because there's nothing else to do after the game finishes

    @tictactoe.error
    async def ttt_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandOnCooldown): # If the error is due to a cooldown
            await ctx.reply(
                embed = discord.Embed(
                    title = "Hold on!",
                    description = f"You can play this game again {discord.utils.format_dt(dt.now() + td(error.retry_after))}",
                    color = discord.Color.red()
                )
            )
        else:
            raise error


async def setup(bot):
    await bot.add_cog(TicTacToe(bot))
