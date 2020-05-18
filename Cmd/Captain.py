from discord.ext import commands
from Model import Model
import itertools
import discord

from Game import State
from Player import MatchRes

class Captain(commands.Cog):
    CMD_RATE = 2
    CMD_COOLDOWN = 10  
    def __init__(self, model):
        self.model = model

    @commands.command(name='pick', help='Pick member to be on your team', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_pick(self, ctx, member : discord.Member):
        if not self.model.ChkIsReg(ctx):
            return

        choosingId = ctx.message.author.id
        choosingPlayer = ctx.message.author.name
        pickedId = member.id
        pickedPlayer = member.name
            
        region = self.model.RegFromPlayer(choosingId)
        if region == None:
            await ctx.send(f'Must be a captain in order to pick')
            return

        if choosingId == pickedId:
            await ctx.send(f'Cannot pick self')
            return

        game = self.model.games[region]
        if game.playerTurn.id != choosingId:
            await ctx.send(f'Not your turn to pick')
            return

        if game.state == State.IN_GAME:
            await ctx.send(f'Game already running')
            return

        if pickedId not in game.PoolIds():
            await ctx.send(f"Player not in player pool")
            return

        game.PickPlayer(pickedId)

        await ctx.send(f'{choosingPlayer} ({game.PlayerRace(pickedId)}) chose {pickedPlayer}')
        await self.model.PickShow(ctx, game)
        await self.model.SetPickTimer(ctx, game)

    @commands.command(name='sub', help='Sub member due to AFK', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_sub(self, ctx, memSub : discord.Member, memSubWith : discord.Member):
        if not self.model.ChkIsReg(ctx):
            return
        if not (self.model.ChkIsRegId(memSub) and self.model.ChkIsRegId(memSubWith)):
            await ctx.send(f'All subbed players must be registered')

        choosingId = ctx.message.author.id
            
        region = self.model.RegFromPlayer(choosingId)
        if region == None:
            await ctx.send(f'Must be a captain in order to sub')
            return

        if memSub.id == choosingId:
            await ctx.send(f'Cannot sub self')
            return

        game = self.model.games[region]
        if game.playerTurn.id != choosingId:
            await ctx.send(f'Not your turn to pick')
            return

        if game.state == State.IN_GAME:
            await ctx.send(f'Game already running')
            return

        if memSub.id not in game.PoolIds():
            await ctx.send(f"{memSub.name} not in player pool")
            return

        #must validate memSubWith.id not in another game already but should already be handled with above check

        pSubWith = self.model.playerDB.Find(memSubWith.id, region)
        game.Sub(memSub, pSubWith)
        await ctx.send(f'{memSub.name} subbed with {memSubWith.name}')
    
    @commands.command(name='rw', help='Captain report win')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_report_win(self, ctx):
        if not self.model.ChkIsReg(ctx):
            return
        await self.model.ReportMatchResult(ctx, MatchRes.WIN, ctx.message.author.id)

    @commands.command(name='rl', help='Captain report loss')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_report_loss(self, ctx):
        if not self.model.ChkIsReg(ctx):
            return
        await self.model.ReportMatchResult(ctx, MatchRes.LOSS, ctx.message.author.id)

    @commands.command(name='rt', help='Captain report tie')
    @commands.cooldown(2, 10)
    async def on_report_tie(self, ctx):
        if not self.model.ChkIsReg(ctx):
            return
        await self.model.ReportMatchResult(ctx, MatchRes.TIE, ctx.message.author.id)

#@client.command(aliases = ['lvl', 'Rank'])
