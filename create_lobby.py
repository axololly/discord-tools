import discord, asyncio
from discord import app_commands, ui, Interaction, ButtonStyle as BS, Button
from discord.ext import commands

class CreateLobbyView(ui.View):
    def __init__(self, orchestrator: discord.Member, limit: int = None):
        super().__init__(timeout = None)
        self.players = [orchestrator] # Set a new list of just the person who made the lobby
        self.limit = limit 

    async def display_players(self, interaction: Interaction):
        embed = discord.Embed(
            title = "Players",
            description = f"There are {len(self.players)}{f' / {self.limit}' if self.limit else ''} in the lobby right now.",
            color = discord.Color.blue()
        )
        embed.add_field(
            name = "Players",
            # List the players like this:
            # 1. ...
            # 2. ...
            # 3. ...
            value = "\n".join([f"{place}. {player.mention}" for place, player in enumerate(self.players, start = 1)])
        )
        await interaction.response.edit_message(view = self, embed = embed) # Update the message with the parsed interaction

    @ui.button(label = "Join Lobby", style = BS.green)
    async def join_lobby(self, interaction: Interaction, button: Button):
        if interaction.user in self.players: # If they're already in the lobby
            await interaction.response.send_message(
                ephemeral = True, embed = discord.Embed(
                    description = "You're already in this lobby!", # Tell the user that
                    color = discord.Color.red()
                )
            )
            return # Cut the code there

        if self.limit and len(self.players) == self.limit: # If a limit is set and the limit is met (the lobby is full)
            await interaction.response.send_message(
                ephemeral = True, embed = discord.Embed(
                    description = "You can't join that lobby because it's full!", # Tell the user the lobby is full
                    color = discord.Color.red()
                )
            )
            return # Cut the code there
        
        self.players.append(interaction.user) # Add the user to the list

        await self.display_players(interaction) # Display a new embed with the updated list
    
    @ui.button(label = "Leave Lobby", style = BS.red)
    async def leave_lobby(self, interaction: Interaction, button: Button):
        if interaction.user not in self.players: # If they are not in the lobby (trying to leave something they're not in)
            await interaction.response.send_message(
                ephemeral = True, embed = discord.Embed(
                    description = "You're not in this lobby!", # Tell the user that
                    color = discord.Color.red()
                )
            )
            return
        
        self.players.remove(interaction.user) # Remove them

        if len(self.players) == 0:
            await interaction.response.edit_message(
                view = None, embed = discord.Embed(
                    title = "This lobby is empty!",
                    description = "Looks like everyone who was in the lobby has left, leaving it empty so I had to close it! Why don't you want to play with me? :(",
                    color = discord.Color.red()
                )
            )
            self.stop() # Stop taking in input because the lobby is closed
            return

        await self.display_players(interaction) # Display the new list

class Lobby(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    lobby = app_commands.Group(name = 'lobby', description = "Do stuff with lobbies.")

    @lobby.command(name = 'create', description = "Create a lobby.")
    async def create(self, interaction: Interaction):
        view = CreateLobbyView(orchestrator = interaction.user, limit = 10) # Create the view
        embed = discord.Embed(
            title = "Loading...",
            description = "Creating the lobby for you...",
            color = discord.Color.dark_embed()
        )
        await interaction.response.send_message(embed = embed, view = view) # Send the embed with the view

        try:
            await asyncio.wait_for(view.wait(), timeout = 30) # Set a hard timeout for how long the lobby will stay open for

        except asyncio.TimeoutError: # When the lobby closes
            view.stop() # Stop listening for view input
            embed = discord.Embed(
                title = "Players",
                description = f"There are {len(self.players)}{f' / {self.limit}' if self.limit else ''} in the lobby right now.",
                color = discord.Color.green()
            )
            embed.add_field(
                name = "Players",
                value = "\n".join([f"{place}. {player.mention}" for place, player in enumerate(self.players, start = 1)])
            )
            
            await interaction.followup.edit_message(view = None, embed = embed) # Update the message with all the people in the lobby

            # You can go further down here with whatever you want

async def setup(bot):
    await bot.add_cog(Lobby(bot))
