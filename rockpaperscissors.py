import discord
from discord import app_commands, ui, Interaction, ButtonStyle as BS, Button
from discord.ext import commands
from _requestplayview import RequestToPlayView

class RockPaperScissorsButton(ui.Button):
    def __init__(self, option: str, emoji: str):
        super().__init__(
            label = option,
            style = BS.blurple,
            emoji = emoji
        )
    
    async def callback(self, interaction: Interaction):
        if interaction.user != self.view.player: # If the person pressing the buttons isn't the player
            await interaction.response.send_message("This isn't for you.", ephemeral = True)
            return

        if self.view.choice: # If they have already decided yet
            await interaction.response.send_message("You already made your choice!", ephemeral = True)
            return
        
        self.view.choice = self.label
        await interaction.response.send_message(f"You played **{self.label}**", ephemeral = True)
        self.view.stop()  

class RockPaperScissorsView(ui.View):
    def __init__(self, player: discord.Member):
        super().__init__(timeout = 20) # Set the timeout
        self.player = player # Set the player
        self.choice = None # Reset the choice made

        for option, emoji in range(3): # Add the option buttons
            self.add_item(RockPaperScissorsButton(option, emoji))

    async def on_callback(self):
        # Disable all the buttons
        for child in self.children:
            child.disabled = True

    async def on_timeout(self):
        await self.on_callback()
        # Timeout message
        await self.message.edit(
            content = None, view = self, embed = discord.Embed(
                title = "⏰  **Timed out!**",
                description = f"How hard is it to press a few buttons, {self.player.mention}?",
                color = 0xff9691
            )
        )

class RockPaperScissors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name = "rockpaperscissors", description = "Play Rock Paper Scissors with another user. Have fun!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def rps(self, interaction: Interaction, opponent: discord.Member = None):
        if not opponent or opponent == interaction.user: # If there's no opponent or the opponent is the person running the command
            await interaction.response.send_message("You can't play with yourself. Go touch grass and find some new friends! :park:", ephemeral = True)
            return
        
        if opponent == self.bot: # If the opponent is the bot
            await interaction.response.send_message("My maker didn't give me arms to play  :x:", ephemeral = True)
            return
        
        view = RequestToPlayView(interaction.user, opponent, game = "Rock Paper Scissors") # Setup the request to play view

        requestToPlay = discord.Embed(
            title = ":mag: Someone wants to play a game of Rock Paper Scissors!",
            description = f"{opponent.mention}, do you want to take up the challenge?",
            color = 0xbffcc6
        )

        # Ask the user if they want to play
        await interaction.response.send_message(
            content = opponent.mention,
            embed = requestToPlay,
            view = view
        )
        view.message = await interaction.original_response() # Get the message attribute
        await view.wait() # Wait for a response

        if not view.value: # If they don't accept, return
            return

        await view.message.delete()

        rpsview1 = RockPaperScissorsView(interaction.user) # Setup the player's view
        
        # Send the game message
        await interaction.response.send_message(
            view = rpsview1, embed = discord.Embed(
                title = "Rock Paper Scissors",
                description = f"""{interaction.user.mention}  \❌\n{opponent.mention}  \❌\n\n{interaction.user.mention}, make your move!""",
                color = 0xc3b1e1
            )
        )
        rpsview1.message = await interaction.original_response() # Get the message attribute
        await rpsview1.wait() # Wait for a response

        if not rpsview1.choice: # If they don't respond, return
            return

        p = rpsview1.choice # Register their choice

        rpsview2 = RockPaperScissorsView(opponent) # Setup the opponent's view
        
        # Update the message with the new view
        await rpsview1.message.edit(
            view = rpsview2, embed = discord.Embed(
                title = "Rock Paper Scissors",
                description = f"""{interaction.user.mention}  \✅\n{opponent.mention}  \❌\n\n{opponent.mention}, make your move!""",
                color = 0xc3b1e1
            )
        )
            
        await rpsview2.wait() # Wait for the opponent's response

        if not rpsview2.choice: # If they don't respond, return
            return

        o = rpsview2.choice

        if p == o: # If it's a draw
            win = 0
        elif p == "rock" and o == "scissors" or p == "paper" and o == "rock" or p == "scissors" and o == "paper": # If player wins
            win = 1
        elif p == "rock" and o == "paper" or p == "paper" and o == "scissors" or p == "scissors" and o == "rock": # If opponent wins
            win = 2
        
        await rpsview1.on_callback() # Disable the buttons on the view

        if win == 0: # Announce the draw
            await rpsview1.message.edit(
                embed = discord.Embed(
                    title = "Draw! <:pain:1203002986331242536>",
                    description = f"""{interaction.user.mention}:  \✅
                                      {opponent.mention}:  \✅
                                      
                                      Looks like a draw! {interaction.user.mention} :handshake: {opponent.mention}""",
                        color = discord.Color.green()
                ), view = rpsview2
            )
            return

        if win == 1: # Announce the player won
            await rpsview1.message.edit(
                embed = discord.Embed(
                    title = "Winner! :trophy:",
                    description = f"""{interaction.user.mention}  \✅
                                      {opponent.mention}  \✅

                                      {interaction.user.mention} won with **{p}** and got some XP! <a:xp:1206668715710742568>""",
                    color = 0xfffaa0
                ), view = rpsview2
            )
            
        if win == 2: # Announce the opponent won
            await rpsview1.message.edit(
                embed = discord.Embed(
                    title = "Winner! <:holymoly:1205945639435903106>",
                    description = f"""{interaction.user.mention}  \✅
                                      {opponent.mention}  \✅
                                  
                                      {opponent.mention} won with **{o}** and got some XP! <a:xp:1206668715710742568>""",
                    color = 0xfffaa0
                ), view = rpsview2
            )

async def setup(bot):
    await bot.add_cog(RockPaperScissors(bot))
