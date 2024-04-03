from discord import ui, Interaction, Member, Embed, Color, Button, ButtonStyle as BS

class RequestToPlayView(ui.View):
    def __init__(self, player: Member, opponent: Member, game: str = None, timeout: int = 20):
        super().__init__()
        self.player = player
        self.opponent = opponent
        self.value = None
        self.timeout = timeout
        self.game = game
    
    async def on_callback(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        await self.on_callback()
        await self.message.edit(
            content = None,
            embed = Embed(
                title = "⏰  **Timed out!**",
                description = "~~" + self.message.embeds[0].description + "~~",
                color = Color.red()
            ), view = self
        )
    
    @ui.button(label = "Accept", style = BS.green)
    async def accept(self, interaction: Interaction, button: Button):
        if interaction.user == self.player:
            await interaction.response.send_message(content = "not you, dingus", ephemeral = True)
        
        elif interaction.user == self.opponent:
            await self.on_callback()
            await interaction.response.edit_message(
                embed = Embed(
                    title = "**Match found!**",
                    description = f":white_check_mark:  {self.opponent.mention} has accepted the challenge.\n Game will begin shortly.",
                    color = Color.green()
                ), view = self
            )

            self.value = True
            self.stop()
        
        else:
            await interaction.response.send_message("not you, dingus", ephemeral = True)
    
    @ui.button(label = "Deny", style = BS.red)
    async def deny(self, interaction: Interaction, button: Button):
        if interaction.user == self.player:
            await interaction.response.edit_message(
                content = self.opponent.mention,
                embed = Embed(
                    title = f":mag: Someone wants to play a game of {self.game}!",
                    description = f":x:  {self.opponent.mention}, {self.player.name} cancelled the challenge.",
                    color = Color.red()
                ), view = None
            )
            self.stop()
        
        elif interaction.user in [self.player, self.opponent]:
            await self.on_callback()
            await interaction.response.edit_message(
                embed = Embed(
                    title = "**Match declined!**",
                    description = f":x:  {self.opponent.mention} has declined the challenge. Sorry bro, not my fault.",
                    color = Color.red()
                ), view = None
            )
            self.stop()
        
        else:
            await interaction.response.send_message("not you, dingus", ephemeral = True)
