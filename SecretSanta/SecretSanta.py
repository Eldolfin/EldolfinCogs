import asyncio

import discord
import redbot.core.config
from redbot.core import commands, bot, checks, Config, data_manager
from datetime import datetime
from random import choice

'''
TODO:
-Logging channel

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


async def reveal_picked(user, picked_user):
    message: discord.Message = await user.send("Vous avez pioché")
    counter: discord.Message = await user.send("**10**")
    for i in range(9):
        await asyncio.sleep(0.7)
        await message.edit(content=message.content + ".")
        await counter.edit(content="**" + str(9 - i) + "**")
    await message.edit(content="**" + picked_user.display_name + "!**")
    await user.send(picked_user.avatar_url)
    await user.send("🎁")
    await counter.delete()


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
    async def setsanta_signup(self, ctx: commands.Context, messageid):
        message = await get_message_by_id(messageid, ctx.guild)
        await message.add_reaction('🎅')
        await ctx.send("Reaction added to message: " + message.content)
        await self.config.guild(ctx.guild).signup_message.set(message.id)

    @secretsanta.command(name="pick")
    async def secretsanta_pick(self, ctx: commands.Context):
        author = ctx.message.author
        await author.trigger_typing()
        if author.id not in (await self.config.guild(ctx.guild).signed_users()):
            await ctx.send("Tu ne t'es pas inscrit au noël canadien!")
            return
        if await self.config.user(author).picked_user() == -1:
            async with self.config.guild(ctx.guild).unpicked_users() as users:
                choosables = users.copy()
                while choosables.count(author.id):
                    choosables.remove(author.id)
                if len(choosables) < 1:
                    await author.send("Personne n'est disponible pour l'instant 😵‍💫")
                    return
                picked_userid = choice(choosables)
                users.remove(picked_userid)
            await self.config.user(author).picked_user.set(picked_userid)
            picked_user = await ctx.guild.fetch_member(picked_userid)
            await reveal_picked(author, picked_user)
        else:
            picked_user = await ctx.guild.fetch_member(await self.config.user(author).picked_user())
            await author.send("Vous avez déjà pioché: " + picked_user.display_name)

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
    async def secretsantaadmin_resetconfig(self, ctx: commands.Context):
        await ctx.trigger_typing()
        await self.config.guild(ctx.guild).signup_message.clear()
        await self.config.guild(ctx.guild).participant_role.clear()
        await ctx.send("Config successfully cleared!")

    @secretsantaadmin.command(name="resetdata")
    async def secretsantaadmin_resetdata(self, ctx: commands.Context):
        await ctx.trigger_typing()
        for userid in await self.config.guild(ctx.guild).signed_users():
            await self.config.user_from_id(userid).clear()
        await self.config.guild(ctx.guild).signed_users.clear()
        await self.config.guild(ctx.guild).unpicked_users.clear()
        await ctx.send("Data successfully cleared!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message: discord.Message = await (await self.bot.fetch_channel(payload.channel_id)).fetch_message(
            payload.message_id)
        # message: discord.Message = reaction.message
        user = payload.member
        guildconf = self.config.guild(message.guild)
        if message.id == await guildconf.signup_message() and user.id not in (await guildconf.signed_users()):
            async with guildconf.signed_users() as users:
                users.append(user.id)

            async with guildconf.unpicked_users() as users:
                users.append(user.id)

            await user.add_roles(
                discord.utils.get(
                    message.guild.roles,
                    id=await guildconf.participant_role()))

            await self.config.user(user).signup_time.set(datetime.now().strftime("%H:%M:%S.%f %d/%b/%Y"))

            await user.send("Bravo tu t'es inscrit au Secret Santa 🎅\n" +
                            "Tu peux ecrire !secretsanta pick pour piocher quelqu'un")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        message: discord.Message = await (await self.bot.fetch_channel(payload.channel_id)).fetch_message(
            payload.message_id)
        reaction = discord.utils.get(message.reactions,emoji="🎅")
        # message: discord.Message = reaction.message
        user = await self.bot.fetch_user(payload.user_id)
        guildconf = self.config.guild(message.guild)
        if message.id == await guildconf.signup_message():
            await asyncio.sleep(5)
            if user not in await reaction.users().flatten():
                await user.send(
                    "La désinscription du SecretSanta n'est pas implémenté (imagine qqlq t'as pioché), demandez à Eldolfin de vous désinscrire au pire")
