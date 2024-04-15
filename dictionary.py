# You can use this cog to search definitions of words using Free Dictionary API.
# Use the base link "https://api.dictionaryapi.dev/api/v2/entries/en/" combined with the word of your choice.
# It will return a status code of 404 if the word is not in the dictionary, like the word "klhasdhnvwa".
# No API keys are needed. The API is entirely free, making it a perfect option.

import discord, aiohttp
from discord import app_commands, ui, Interaction, ButtonStyle as BS
from discord.ext import commands

class DictionaryView(ui.View):
    # These are the shortened word classes that will be displayed in the embed.
    # This will shorten "verb" to "v.", "noun" to "n." and so on.
    # This is done to save space in the embed.
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
    
    def __init__(self, definitions: list): # Take the definitions as a parameter
        super().__init__(timeout = 30) # Set the timeout to 30 seconds
        self.current_page = 0 # The current page of the definitions
        self.definitions = definitions # The import snippet of the JSON document from the API response data
        # The total number of pages in the definitions.
        # This is calculated by subtracting 2 from the total number of values in the first meaning.
        # I'm gonna be honest, I have no idea why you have to subtract 2. Just worked. ¯\_(ツ)_/¯
        self.page_count = len(self.definitions['meanings'][0].values()) - 2

    async def on_timeout(self) -> None:
        await self.message.edit(view = None) # Remove the button when the view times out

    async def create_page(self) -> discord.Embed:
        # Create the embed to be displayed
        page = discord.Embed(
            # The word and its phonetic pronunciation, e.g. "word (/ˈwərd/)"
            title = f"{self.definitions['word']}" + f" ({self.definitions['phonetic']})" if self.definitions['phonetic'] else '',
            # Show the shortened word class, e.g. "v." for "verb"
            description = self.shortened_word_classes[self.definitions['meanings'][self.current_page]['partOfSpeech']],
            color = discord.Color.blurple(), # Set the color to blurple
            timestamp = discord.utils.utcnow(), # Set the timestamp to the current time, but formatted
            url = self.definitions['sourceUrls'][0] # Set the URL to the source URL so users can see more
        )

        # Show the definition of the word
        page.add_field(
            name = 'Definition',
            value = '\n'.join([f'{i + 1}. {definition['definition']}' # Display a numbered list of all definitions for that page.
                    for i, definition in enumerate(self.definitions['meanings'][self.current_page]['definitions'])])
        )

        # If there's an example, show it
        if self.definitions['meanings'][self.current_page].get('example'):
            page.add_field(
                name = 'Example',
                value = '"' + self.definitions['meanings'][self.current_page]['example'] + '"' # Show an example in quotes
            )
        
        # Show the current page number out of the total number of pages
        page.set_author(name = self.definitions['word'] + f': {self.current_page + 1} out of {self.page_count + 1}')
        page.set_footer(text = "Created using Free Dictionary API")

        # Return the created embed
        return page
    
    async def display_page(self) -> None:
        if self.current_page == 0: # If you're on the first page
            for button in self.children[:2]: # Disable the first two buttons
                button.disabled = True
            
            for button in self.children[2:4]: # Enable the last two buttons
                button.disabled = False
        
        elif self.current_page == self.page_count: # If you're on the last page
            for button in self.children[2:4]: # Disable the last two buttons
                button.disabled = True
            
            for button in self.children[:2]: # Enable the first two buttons
                button.disabled = False

        else: # Otherwise, like if you're on page 2 of 3, you can go left or right, so enable all buttons
            for button in self.children:
                button.disabled = False

        page = await self.create_page() # Create the page to be displayed

        # Edit the message with the new page and a view if there's more than 1 meaning, otherwise don't bother with the view
        await self.message.edit(embed = page, view = self if self.page_count > 1 else None)
    
    @ui.button(label = '<<', style = BS.grey, disabled = True) # Starts off disabled
    async def go_to_start(self, interaction: Interaction, _):
        self.current_page = 0 # Set the current page to 0
        await interaction.response.defer() # Defer the interaction
        await self.display_page() # Display the page

    @ui.button(label = 'Back', style = BS.primary, disabled = True) # Starts off disabled
    async def go_to_previous(self, interaction: Interaction, _):
        self.current_page -= 1 if self.current_page > 0 else 0 # Go to the previous page if you're not on the first page
        await interaction.response.defer() # Defer the interaction
        await self.display_page() # Display the page

    @ui.button(label = 'Next', style = BS.primary)
    async def go_to_next(self, interaction: Interaction, _):
        self.current_page += 1 if self.current_page < self.page_count else 0 # Go to the next page if you're not on the last page
        await interaction.response.defer() # Defer the interaction
        await self.display_page() # Display the page
    
    @ui.button(label = '>>', style = BS.grey)
    async def go_to_end(self, interaction: Interaction, _):
        self.current_page = self.page_count # Set the current page to the last page
        await interaction.response.defer() # Defer the interaction
        await self.display_page() # Display the page

    @ui.button(label = 'Quit', style = BS.red)
    async def _quit(self, _, __):
        await self.message.delete() # Delete the message
        self.stop() # Stop the view

class Dictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # Set the bot instance

    # Allow the command to be installed in guilds and DMs
    @app_commands.allowed_installs(guilds = True, users = True)
    # Allow the command to be used in guilds, DMs, and private channels
    @app_commands.allowed_contexts(guilds = True, dms = True, private_channels = True)
    # Create the dictionary command with an accompanying name and description
    @app_commands.command(name = 'dictionary', description = 'Search for a word in the dictionary')
    # Give the word parameter a description to show when the command is being run.
    @app_commands.describe(word = 'The word to search for. Example: "hello"')
    async def dictionary(self, interaction: Interaction, word: str): # Take a word parameter
        async with aiohttp.ClientSession() as session: # Open an aiohttp client session
            async with session.get('https://api.dictionaryapi.dev/api/v2/entries/en/' + word) as response: # Get the API response
                if response.status == 404: # If the word isn't found
                    error_embed = discord.Embed(
                        title = "Word not found!",
                        description = "Looks like that word isn't in the dictionary. Please try again.",
                        color = discord.Color.red(),
                        timestamp = discord.utils.utcnow()
                    )
                    # Notify the user it's not a valid word.
                    return await interaction.response.send_message(embed = error_embed, ephemeral = True)

                # Get the JSON data from the API response
                definitions = await response.json()
        
        # Construct the view
        view = DictionaryView(definitions = definitions[0])

        # Send the message with the view
        await interaction.response.send_message(embed = await view.create_page(), view = view)        
        
        # Set the message attribute of the view to the original response.
        # This is done so the view can be edited later on.
        # Simply setting the message attribute to interaction.response.send_message() doesn't work.
        # This is because .send_message() does not return anything, so the message attribute would be None.
        # Therefore, nothing could be performed on the message.
        view.message = await interaction.original_response()


async def setup(bot): # Setup function
    await bot.add_cog(Dictionary(bot)) # Add the cog to the bot

if __name__ == '__main__': # If this isn't the main file
    import main # Import the main file
