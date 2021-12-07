import discord
import redbot.core.config
from redbot.core import commands, bot, checks, Config, data_manager
from datetime import datetime
from random import choice
'''
TODO:
-Envoyer la pfp de la personne piochée
-Decompte lorsqu'on pioche?
-dans userconf un haspicked
-check haspicked lors du pick
-
'''

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
            "signed_users": [],
            "unpicked_users": [],
        }
        userconf = {
            "signup_time": "never",
            "picked_user": -1,
        }
        self.config.register_user(**userconf)
        self.config.register_guild(**guildconf)

    @commands.group()
    @commands.guild_only()
    @commands.admin()
    async def secretsantaadmin(self, ctx: commands.Context):
        pass

    @secretsantaadmin.group(name="set")
    async def secretsantaadmin_set(self, ctx):
        pass

    @commands.group()
    @commands.guild_only()
    async def secretsanta(self, ctx: commands.Context):
        pass

    @secretsantaadmin_set.command(name="role")
    async def setsanta_role(self, ctx: commands.Context, role: discord.Role):
        await ctx.send("Role set: " + role.name)
        await self.config.guild(ctx.guild).participant_role.set(role.id)

    @secretsantaadmin_set.command(name="signup_message")
    async def setsanta_reaction(self, ctx: commands.Context, message: discord.Message):
        # if len(message.reactions) < 1:
        #     await ctx.send("This message has no reaction!")
        #     return
        await message.add_reaction('🎅')
        await ctx.send("Reaction added to message: " + message.content)
        await self.config.guild(ctx.guild).signup_message.set(message.id)

    @secretsanta.command(name="pick")
    async def secretsanta_pick(self, ctx: commands.Context):
        await ctx.message.author.trigger_typing()
        async with self.config.guild(ctx.guild).unpicked_users() as users:
            choosables = users.copy()
            while choosables.count(ctx.message.author.id):
                choosables.remove(ctx.message.author.id)
            if (len(choosables) < 1):
                await ctx.message.author.send("Personne n'est disponible pour l'instant 😵‍💫")
                return
            picked_userid = choice(choosables)
            users.remove(picked_userid)
        picked_user = await ctx.guild.fetch_member(picked_userid)
        await ctx.message.author.send("Vous avez pioché: " + picked_user.display_name)

    @secretsantaadmin.command(name="getconf")
    async def secretsantaadmin_getconf(self, ctx: commands.Context):
        await ctx.trigger_typing()
        signup_message = await get_message_by_id(await self.config.guild(ctx.guild).signup_message(), ctx.guild)
        roleid = await self.config.guild(ctx.guild).participant_role()
        role = discord.utils.get(ctx.guild.roles, id=roleid)
        await ctx.send("Current settings:" +
                       "\nrole: " + role.name +
                       "\nsignup_message: " + signup_message.content)

    @secretsantaadmin.command(name="resetconfig")
    async def secretsantaadmin_resetconfig(self, ctx:commands.Context):
        await ctx.trigger_typing()
        for userid in await self.config.guild(ctx.guild).signed_users():
            await self.config.user_from_id(userid).clear()
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Config successfully cleared!")


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):

        message: discord.Message = reaction.message
        guildconf = self.config.guild(message.guild)
        if message.id == await guildconf.signup_message() and user.id not in await guildconf.signed_users():
            async with guildconf.signed_users() as users:
                users.append(user.id)

            async with guildconf.unpicked_users() as users:
                users.append(user.id)

            await self.config.user(user).signup_time.set(datetime.now().strftime("%H:%M:%S.%f %d/%b/%Y"))

            await user.send("Bravo tu t'es inscrit au Secret Santa 🎅\n" +
                            "Tu peux ecrire !secretsanta pick pour piocher quelqu'un")

