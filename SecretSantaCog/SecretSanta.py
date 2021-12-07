import discord
from redbot.core import commands, bot, checks, Config, data_manager


def setup(bot):
    bot.add_cog(SecretSanta(bot))


async def get_message_by_id(id, guild: discord.Guild):
    for channel in guild.text_channels:
        try:
            message = await channel.fetch_message(id)
            return message
        except discord.NotFound:
            pass
    return None


class SecretSanta(commands.Cog):
    """My custom cog"""

    def __init__(self, bot: bot.Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        # data_manager.load_basic_configuration("Testing_redbot")
        self.config = Config.get_conf(self, identifier=2026202120)
        guildconf = {
            "signup_message": -1,
            "participant_role": -1,
            "signed_users": []
        }
        userconf = {
            "signup_time": -1,
            "picked_user": -1
        }
        self.config.register_user(**userconf)
        self.config.register_guild(**guildconf)

    @commands.group()
    @commands.guild_only()
    @commands.admin()
    async def setsanta(self, ctx: commands.Context):
        pass

    @commands.group()
    async def secretsanta(self, ctx: commands.Context):
        pass

    @setsanta.command(name="role")
    async def setsanta_role(self, ctx: commands.Context, role: discord.Role):
        await ctx.send("Role set: " + role.name)
        await self.config.guild(ctx.guild).participant_role.set(role.id)

    @setsanta.command(name="signup_message")
    async def setsanta_reaction(self, ctx: commands.Context, message: discord.Message):
        # if len(message.reactions) < 1:
        #     await ctx.send("This message has no reaction!")
        #     return
        await message.add_reaction('🎅')
        await ctx.send("Reaction added to message: " + message.content)
        await self.config.guild(ctx.guild).signup_message.set(message.id)

    @secretsanta.command(name="pick")
    @commands.dm_only()
    async def secretsanta_pick(self, ctx: commands.Context):
        await ctx.send("You picked: ")

    @commands.command()
    @commands.admin()
    async def getsantaconf(self, ctx: commands.Context):
        await ctx.trigger_typing()
        signup_message = await get_message_by_id(await self.config.guild(ctx.guild).signup_message(), ctx.guild)
        roleid = await self.config.guild(ctx.guild).participant_role()
        role = discord.utils.get(ctx.guild.roles, id=roleid)
        await ctx.send("Config:" +
                       "\nrole: " + role.name +
                       "\nsignup_message: " + signup_message.content)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        message: discord.Message = reaction.message
        async with self.config.signed_users() as userlist:
            userlist.append(user.id)
        if message.id == await self.config.guild(message.guild).signup_message():
            await user.send("Bravo tu t'es inscrit au Secret Santa 🎅\n" +
                            "Tu peux ecrire !secretsanta pick pour piocher quelqu'un")
