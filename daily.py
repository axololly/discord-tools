import discord, asqlite, sqlite3, time
from discord import app_commands, Interaction
from discord.ext import commands
from datetime import datetime as dt, timedelta as td

class Daily(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool: asqlite.Pool = bot.pool
    
    @app_commands.command(name = 'daily', description = "Collect your daily coins.")
    async def daily(self, interaction: Interaction):
        async with self.pool.acquire() as conn: # Acquire a connection from the pool
            try:
                # Retrieve data from the "daily" table
                # Can change if another table has these details
                req = await conn.execute("SELECT * FROM daily WHERE user_id = ?", (interaction.user.id,))
            
            except sqlite3.OperationalError: # the table doesn't exist, so create it
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS daily (
                        user_id INTEGER UNIQUE NOT NULL
                        last_run INTEGER NOT NULL,
                        streak INTEGER NOT NULL DEFAULT 1
                    )
                """)
            
            row = await req.fetchone() # Fetch the data
        
            if not row: # If the data doesn't exist
                await conn.execute( # Add the data to the table
                    "INSERT INTO daily (user_id, last_run) VALUES (?, ?)",
                    (interaction.user.id, int(time.time()))
                )
                # Add coins to a bank account
                return
            
            # Get a datetime from the timestamp in the table
            last_run = dt.fromtimestamp(row['last_run'])
            # Get the datetime of when it turns the day after the command was last run
            can_run_again = dt.strptime(str(last_run.date()), "%Y-%m-%d") + td(days = 1)
            # Find the difference in days to when that command was last run
            diff: int = (dt.now() - can_run_again).days

            if diff == -1: # already run the command today
                await interaction.response.send_message(
                    ephemeral = True, embed = discord.Embed(
                        title = "You ran this command today!",
                        description = f"You can get your daily coins again {discord.utils.format_dt(can_run_again, style = "R")}.\n\nHave fun!",
                        color = discord.Color.red()
                    )
                )
            elif diff == 0: # can run the command again (it's the following day)
                coins_per_day = ... # change accordingly

                async with self.pool.acquire() as conn:
                    # change accordingly
                    await conn.execute("UPDATE accounts SET wallet = wallet + ? WHERE user_id = ?", (coins_per_day, interaction.user.id))
                    # update the table with the new streak count
                    await conn.execute("UPDATE daily SET streak = streak + 1 WHERE user_id = ?", (interaction.user.id,))

                await interaction.response.send_message(
                    ephemeral = True, embed = discord.Embed(
                        title = "You claimed your coins!",
                        # This can be formatted like {coins_per_day:,} if it's an integer
                        description = f"You claimed today's coins, getting you {coins_per_day} in your pocket. Have fun and don't forget to claim this again!"
                    )
                )
            else: # streak has been broken (it's been more than a day)
                await interaction.response.send_message(
                    ephemeral = True, embed = discord.Emebd(
                        title = "Your streak ran out!",
                        description = f"You forgot to claim your daily, so you lost your **{row['streak']}** day streak.\nYou last ran this command {discord.utils.format_dt(last_run, style = 'R')}",
                        color = discord.Color.red()
                    )
                )

                async with self.pool.acquire() as conn:
                    await conn.execute("DELETE FROM daily WHERE user_id = ?", (interaction.user.id,)) # Delete the streak entry from the table, since there's no point in keeping it


async def setup(bot):
    await bot.add_cog(Daily(bot))
