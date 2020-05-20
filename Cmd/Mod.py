from discord.ext import commands
from Model import Model
import itertools
import discord

from Game import State
from Player import Player, MatchRes, Race
from Region import Region
from Utility import CodeB, CodeSB

class Mod(commands.Cog):     
    CMD_RATE = 5
    CMD_COOLDOWN = 20
    def __init__(self, model):
        self.model = model
        
    @commands.command(name='unreg', help='Unregister user with the server and delete stats', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_unregister(self, ctx, member : discord.Member, region : Region = Region(Region.ALL)):
        self.model.playerDB.UnRegister(member.id, region.region)
        await ctx.send(f'{member.name} successfully unregistered on {region.region}')

    @commands.command(name='forceend', help='Force game to end on region', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_force_end(self, ctx, region : Region = Region(Region.ALL)):
        if region.region == Region.ALL:
            for reg in Region.REGIONS:
                self.on_force_end(ctx, reg)
        elif self.model.games[region.region]:
            await self.model.ReportMatchResult(ctx, MatchRes.TIE, self.model.games[region.region].zergCapt.id)

    @commands.command(name='setelo', help="Set player's elo to # on region for race (Z/T/A)", ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_set_elo(self, ctx, member : discord.Member, region : Region, race : Race, elo : float):
        playerName = member.name
        regions = region.ToList()
        races = race.ToList()

        for reg in regions:
            usPlayer = self.model.playerDB.Find(member.id, reg)
            if usPlayer == None:
                await ctx.send(CodeSB(f'Player {playerName} not registered'))
                return

            if not usPlayer.lastPlayed:
                usPlayer.SetPlayed()

            for r in races:
                usPlayer.elo[r] = elo
            self.model.playerDB.UpdateStats(usPlayer)
        await ctx.send(CodeSB(f"Updated {playerName}'s' elo to {usPlayer.elo[races[0]]} for {', '.join(races)} on {', '.join(regions)}"))
    
    @commands.command(name='setstats', help="Set player's stats on region for race (Z/T/A)", ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_set_stats(self, ctx, member : discord.Member, region : Region, race : Race, wins : int, loses : int, ties : int):
        playerName = member.name
        regions = region.ToList()
        races = race.ToList()

        for reg in regions:
            usPlayer = self.model.playerDB.Find(member.id, reg)
            if usPlayer == None:
                await ctx.send(f'Player {playerName} not registered')
                return

            if not usPlayer.lastPlayed:
                usPlayer.SetPlayed()

            for r in races:
                usPlayer.wins[r] = wins
                usPlayer.loses[r] = loses
                usPlayer.ties[r] = ties
            self.model.playerDB.UpdateStats(usPlayer)

        await ctx.send(CodeSB(f"Updated {playerName}'s' wins={usPlayer.wins[races[0]]}, loses={usPlayer.loses[races[0]]}, ties={usPlayer.ties[races[0]]} for {', '.join(races)} on {', '.join(regions)}"))
    
    @commands.command(name='queue_bot', help='Queue # of bots on region', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_queue_bot(self, ctx, region : Region, count : int):
        self.model.CreateStubs(region.region, count)
        embed = discord.Embed(colour = discord.Colour.blue(), description = self.model.QueueStatus())
        await ctx.channel.send(content=CodeSB(f'Queued {count} bots on {region.region}'), embed=embed)

    @commands.command(name='queue_flush', help='Flush queue on region', ignore_extra=False)
    @commands.has_role('MOD')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_queue_flush(self, ctx, region : Region = Region(Region.ALL)):
        self.model.queues.clear(region.region)
        embed = discord.Embed(colour = discord.Colour.blue(), description = self.model.QueueStatus())
        await ctx.channel.send(content=CodeSB(f'Queues cleared on: {", ".join(region.ToList())}'), embed=embed)

    @commands.command(name='addp', help=f'Add player to queue on region (NA/EU/ALL = default); Timeout={Model.QUEUE_TIMEOUT} mins', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_addp(self, ctx, member : discord.Member, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsRegId(member.id):
            for reg in Region.REGIONS:
                self.model.playerDB.Register(Player(member.id, reg))

        await self.model.AddPlayerQueue(ctx, member.name, member.id, region)

    @commands.command(name='delp', aliases = ['remp'], help='Remove player from queue on region (NA/EU/ALL = default)', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_removep(self, ctx, member : discord.Member, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        await self.model.RemPlayerQueue(ctx, member.name, member.id, region)

    @commands.command(name='addsubp', help='Allow player to be a potential sub on region (captains must already be picking)')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_subp(self, ctx, member : discord.Member, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        await self.model.AddPlayerSub(ctx, member.name, member.id, region)

    @commands.command(name='delsubp', aliases = ['remsubp'], help='Remove player as potential sub on region')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_del_subp(self, ctx, member : discord.Member, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        await self.model.RemPlayerSub(ctx, member.name, member.id, region)