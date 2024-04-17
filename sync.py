# This goes in your main .py file
@bot.command()
async def sync(ctx):
    try:
        synced = bot.tree.sync()
    except:
        error = traceback.format_exc()
        embed = discord.Embed(
            title = "An error occurred!",
            description = "Looks like something went wrong! Take a look below.",
            color = discord.Color.red()
        )
        embed.add_field(
            name = "Error",
            value = f"'''py\n{error}\n'''"
        )
    else:
        embed = discord.Embed(
            title = "Synced successfully!",
            description = f"Synced {synced} commands successfully.",
            color = discord.Color.green()
        )
        embed.add_field(
            name = "Commands",
            value = "\n".join([f"- {cmd.name}  {':white_check_mark:' if cmd in synced else ':x:'}" for cmd in bot.commands])
        )
    finally:
        await ctx.reply(embed = embed)
