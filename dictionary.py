# You can use this cog to search definitions of words using Free Dictionary API.
# Use the base link "https://api.dictionaryapi.dev/api/v2/entries/en/" combined with the word of your choice.
# It will return a status code of 404 if the word is not in the dictionary, like the word "klhasdhnvwa".
# No API keys are needed. The API is entirely free, making it a perfect option.

import discord, aiohttp
from discord import app_commands, ui, Interaction, InteractionMessage, Button, ButtonStyle as BS
from discord.ext import commands

class DictionaryView(ui.View):
    children: list[Button] # type: ignore
    message: InteractionMessage
    
    shortened_word_classes = {
        'noun': 'n.',
        'verb': 'v.',
        'adjective': 'adj.',
        'adverb': 'adv.',
        'pronoun': 'pron.',
        'preposition': 'prep.',
        'conjunction': 'conj.',
        'interjection': 'interj.'
    }
    
    def __init__(self, definitions: dict):
        super().__init__(timeout = 30)
        self.current_page = 0
        self.definitions = definitions
        self.page_count = len(self.definitions['meanings'][0].values()) - 2

    async def on_timeout(self) -> None:
        await self.message.edit(view = None)

    async def create_page(self) -> discord.Embed:
        _phonetic = self.definitions.get('phonetic')
        phonetic = f"({_phonetic})" if _phonetic else ''
       
        page = discord.Embed(
            title = f"{self.definitions['word']} {phonetic}",
            description = self.shortened_word_classes[self.definitions['meanings'][self.current_page]['partOfSpeech']],
            color = discord.Color.blurple(),
            timestamp = discord.utils.utcnow(),
            url = self.definitions['sourceUrls'][0]
        )
       
        page.add_field(
            name = 'Definition',
            value = '\n'.join([f'{i + 1}. {definition['definition']}'
                    for i, definition in enumerate(self.definitions['meanings'][self.current_page]['definitions'])])
        )
       
        if self.definitions['meanings'][self.current_page].get('example'):
            page.add_field(
                name = 'Example',
                value = '"' + self.definitions['meanings'][self.current_page]['example'] + '"'
            )
       
        page.set_author(name = self.definitions['word'] + f': {self.current_page + 1} out of {self.page_count + 1}')
        page.set_footer(text = "Created using Free Dictionary API")
       
        return page
    
    async def display_page(self) -> None:
        # Can only go right
        if self.current_page == 0:
            for button in self.children[:2]:
                button.disabled = True
            
            for button in self.children[2:4]:
                button.disabled = False
        
        # Can only go left
        elif self.current_page == self.page_count:
            for button in self.children[2:4]:
                button.disabled = True
            
            for button in self.children[:2]:
                button.disabled = False

        # Can go either way
        else:
            for button in self.children:
                button.disabled = False
       
        await self.message.edit(
            embed = await self.create_page(),
            view = self if self.page_count > 1 else None
        )
    
    @ui.button(label = '<<', style = BS.grey, disabled = True)
    async def go_to_start(self, interaction: Interaction, _):
        self.current_page = 0
        await interaction.response.defer()
        await self.display_page()

    @ui.button(label = 'Back', style = BS.primary, disabled = True)
    async def go_to_previous(self, interaction: Interaction, _):
        self.current_page -= 1 if self.current_page > 0 else 0
        await interaction.response.defer()
        await self.display_page()

    @ui.button(label = 'Next', style = BS.primary)
    async def go_to_next(self, interaction: Interaction, _):
        self.current_page += 1 if self.current_page < self.page_count else 0
        await interaction.response.defer()
        await self.display_page()
    
    @ui.button(label = '>>', style = BS.grey)
    async def go_to_end(self, interaction: Interaction, _):
        self.current_page = self.page_count
        await interaction.response.defer()
        await self.display_page()

    @ui.button(label = 'Quit', style = BS.red)
    async def _quit(self, _, __):
        await self.message.delete()
        self.stop()

class Dictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name = 'define', description = 'Search for a word in the dictionary.')
    @app_commands.describe(word = 'The word to search for. Example: "hello"')
    async def define_word(self, interaction: Interaction, word: str):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.dictionaryapi.dev/api/v2/entries/en/' + word) as response:
                if response.status == 404:
                    error_embed = discord.Embed(
                        title = "Word not found!",
                        description = "Looks like that word isn't in the dictionary. Please try again.",
                        color = discord.Color.red(),
                        timestamp = discord.utils.utcnow()
                    )
                    
                    return await interaction.response.send_message(
                        embed = error_embed,
                        ephemeral = True
                    )

                
                definitions = await response.json()
        
        view = DictionaryView(definitions = definitions[0])

        await interaction.response.send_message(
            embed = await view.create_page(),
            view = view
        )
        
        view.message = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(Dictionary(bot))
