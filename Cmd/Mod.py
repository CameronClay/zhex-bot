from discord.ext import commands
from Model import Model
import itertools
import discord

from Game import State
from Player import MatchRes
import Region

class Mod(commands.Cog):     
    def __init__(self, model):
        self.model = model
        
    @commands.command(name='unreg', help='Unregister user with the server and delete stats', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(2, 10)
    async def on_unregister(self, ctx, member : discord.Member, region : str = Region.ALL):
        self.model.playerDB.UnRegister(member.id, region)
        await ctx.send(f'{member.name} successfully unregistered on {region}')

    @commands.command(name='forceend', help='Force game to end on region', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(2, 10)
    async def on_force_end(self, ctx, region : str = Region.ALL):
        if region == Region.ALL:
            for reg in Region.REGIONS:
                self.on_force_end(ctx, reg)
        elif self.model.games[region]:
            await self.model.ReportMatchResult(ctx, MatchRes.TIE, self.model.games[region].zergCapt.id)

    @commands.command(name='setelo', help="Set player's elo to #", ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(2, 10)
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
    @commands.cooldown(2, 10)
    async def on_set_stats(self, ctx, member : discord.Member, region : str, wins : int, loses : int):
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
    @commands.cooldown(2, 10)
    async def on_queue_bot(self, ctx, region : str, count : int):
        self.model.CreateStubs(region, count)
        await ctx.send(f'Queued {count} bots on {region}')
    #@commands.command(name='reset', help='Reset bot (does not clear any stats)')
    #@commands.has_role('MOD')
    #@commands.cooldown(2, 10)
    #async def on_reset(self, ctx):
    #    await self.model.reset()