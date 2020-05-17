from discord.ext import commands
from Model import Model
import itertools
import discord
from datetime import datetime

from Game import Game, State
from Player import Player, MatchRes
import Region

class General(commands.Cog):     
    def __init__(self, model):
        self.model = model

    @commands.command(name='reg', help='Register with the server to play private games (registration is required to run all other commands)')
    @commands.cooldown(2, 10)
    async def on_register(self, ctx):
        playerId = ctx.message.author.id
        playerName = ctx.message.author.name

        registeredRegs = []
        for reg in Region.REGIONS:
            res = self.model.playerDB.IsRegistered(playerId, reg)
            if not res:
                self.model.playerDB.Register(Player(playerId, reg))
                registeredRegs.append(reg)

        if len(registeredRegs) == 0:
            await ctx.send(f'{playerName} already registered')
            return
        else:
            await ctx.send(f'{playerName} successfully registered on {registeredRegs}')

    @commands.command(name='add', help='Add to queue on region (NA/EU/ALL = default)')
    @commands.cooldown(2, 10)
    async def on_add(self, ctx, region : str ='ALL'):
        if not self.model.ChkIsReg(ctx):
            return

        player = ctx.message.author.name
        playerId = ctx.message.author.id

        if region == Region.ALL:
            for reg in Region.REGIONS:
                #if player not in queues[reg].Ids:
                if not any((self.model.games[newReg] != None and self.model.games[newReg].IsPlaying(playerId) \
                for newReg in Region.REGIONS)): #necessary if a player causes a game to start and queued on both Region.REGIONS
                    await self.on_add(ctx, reg)
            return
                    
        if region in Region.REGIONS:
            if True: #playerId not in queues[region].Ids:
                if len(self.model.queues[region]) == Game.N_PLAYERS and \
                self.model.games[region].state == State.IN_GAME:
                    await ctx.send(f"{region}'s queue is full")
                    return
                self.model.queues.add(region, playerId)
                await ctx.send(f'{player} added to {region} {len(self.model.queues[region])}/{Game.N_PLAYERS}')

                if len(self.model.queues[region]) == Game.N_PLAYERS:
                    await self.model.StartTeamPick(ctx, region)
            else:
                await ctx.send(f'{player} already added to {region}')
        else:
            await ctx.send('Invalid region, expected: ' + '/'.join(Region.REGIONS))
            return
                
    @commands.command(name='rem', help='Remove from current queues')
    @commands.cooldown(2, 10)
    async def on_remove(self, ctx):
        if not self.model.ChkIsReg(ctx):
            return

        playerId = ctx.message.author.id
        playerName = ctx.message.author.name

        self.model.queues.remove_all(Region.ALL, playerId)
        await ctx.send(f'{playerName} removed from all queues!')
        
    @commands.command(name='stats', help='Retreive stats of player')
    @commands.cooldown(2, 10)
    async def on_stats(self, ctx, member : discord.Member):
        if not self.model.ChkIsReg(ctx):
            return

        playerName = member.name

        embed = discord.Embed(title=f"Stats {playerName}")
        for region in Region.REGIONS:
            usPlayer = self.model.playerDB.Find(member.id, region)
            if usPlayer and usPlayer.lastPlayed:
                embed.add_field(name=region, value=f"Win %: {usPlayer.Ratio * 100 :.1f}%, Elo: {int(usPlayer.elo)}, Games: {usPlayer.games}, \
                Wins: {usPlayer.wins}, Loses: {usPlayer.loses}, Last played: {usPlayer.lastPlayed} UTC")
        await ctx.channel.send(content=None, embed=embed)

    @commands.command(name='status', help='Query status of queue and any running games')
    @commands.cooldown(2, 10)
    async def on_status(self, ctx):
        if not self.model.ChkIsReg(ctx):
            return

        for region, queue in self.model.queues:
            queued = self.model.IdsToNames(queue.keys())
            embed = discord.Embed(title=f"Status of {region}", description=f"Queued {len(queue)}/{Game.N_PLAYERS}\n Players: {queued}")
            if self.model.games[region] != None and self.model.games[region].state == State.IN_GAME:
                game = self.model.games[region]
                zerg = self.model.IdsToNames(game.zerg.Ids)
                terran = self.model.IdsToNames(game.terran.Ids)
                runningDuration = int(game.RunningDuration().total_seconds() / 60)
                embed.add_field(name=f"Running for {runningDuration} min", value=f"Zerg: {zerg}\nTerran: {terran}")
            await ctx.channel.send(content=None, embed=embed)