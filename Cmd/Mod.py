from discord.ext import commands
from Model import Model
import itertools
import discord

from Game import State
from Player import MatchRes
import Region
from Utility import CodeB, CodeSB

class Mod(commands.Cog):     
    CMD_RATE = 5
    CMD_COOLDOWN = 20
    def __init__(self, model):
        self.model = model
        
    @commands.command(name='unreg', help='Unregister user with the server and delete stats', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_unregister(self, ctx, member : discord.Member, region : str = Region.ALL):
        if not await self.model.ValidateReg(ctx, region):
            return

        self.model.playerDB.UnRegister(member.id, region)
        await ctx.send(f'{member.name} successfully unregistered on {region}')

    @commands.command(name='forceend', help='Force game to end on region', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_force_end(self, ctx, region : str = Region.ALL):
        if not await self.model.ValidateReg(ctx, region):
            return

        if region == Region.ALL:
            for reg in Region.REGIONS:
                self.on_force_end(ctx, reg)
        elif self.model.games[region]:
            await self.model.ReportMatchResult(ctx, MatchRes.TIE, self.model.games[region].zergCapt.id)

    @commands.command(name='setelo', help="Set player's elo to #", ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_set_elo(self, ctx, member : discord.Member, region : str, elo : float):
        playerName = member.name

        usPlayer = self.model.playerDB.Find(member.id, region)
        if usPlayer == None:
            await ctx.send(f'Player {playerName} not registered')

        usPlayer.elo = elo
        self.model.playerDB.UpdateStats(usPlayer)
        await ctx.send(f"Updated {playerName}'s' elo on {region} to {usPlayer.elo}")

    
    @commands.command(name='setstats', help="Set player's stats", ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_set_stats(self, ctx, member : discord.Member, region : str, wins : int, loses : int):
        if not await self.model.ValidateReg(ctx, region):
            return

        playerName = member.name

        usPlayer = self.model.playerDB.Find(member.id, region)
        if usPlayer == None:
            await ctx.send(f'Player {playerName} not registered')

        usPlayer.games = usPlayer.games - (usPlayer.wins + usPlayer.loses) + (wins + loses)
        usPlayer.wins = wins
        usPlayer.loses = loses

        self.model.playerDB.UpdateStats(usPlayer)
        await ctx.send(f"Updated {playerName}'s' elo on {region} to {usPlayer.elo}")
    
    @commands.command(name='queue_bot', help='Queue # of bots on region', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_queue_bot(self, ctx, region : str, count : int):
        if not await self.model.ValidateReg(ctx, region):
            return

        self.model.CreateStubs(region, count)
        embed = discord.Embed(colour = discord.Colour.blue(), description = self.model.QueueStatus())
        await ctx.channel.send(content=CodeSB(f'Queued {count} bots on {region}'), embed=embed)

    @commands.command(name='queue_flush', help='Flush queue on region', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_queue_flush(self, ctx, region : str):
        if not await self.model.ValidateReg(ctx, region):
            return

        regions = Region.ToList(region)

        self.model.queues.clear(region)
        embed = discord.Embed(colour = discord.Colour.blue(), description = self.model.QueueStatus())
        await ctx.channel.send(content=CodeSB(f'Queues cleared on: {", ".join(regions)}'), embed=embed)