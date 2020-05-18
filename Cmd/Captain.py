from discord.ext import commands
from Model import Model
import itertools
import discord

from Game import State
from Player import MatchRes
import Region

class Captain(commands.Cog):
    CMD_RATE = 2
    CMD_COOLDOWN = 10  
    def __init__(self, model):
        self.model = model

    #returns game if able to pick a player (only enforces not picking self)
    async def can_pick(self, ctx, choosingId, choosingPlayer, pickedId):
        if not (self.model.ChkIsRegId(choosingId) and self.model.ChkIsRegId(pickedId)):
            return None

        region = self.model.RegFromPlayer(choosingId)
        if region == None:
            await ctx.send(f'Must be a captain in order to pick')
            return None

        if choosingId == pickedId:
            await ctx.send(f'Cannot pick self')
            return None

        game = self.model.games[region]
        if game.playerTurn.id != choosingId:
            await ctx.send(f'Not your turn to pick')
            return None

        if game.state == State.IN_GAME:
            await ctx.send(f'Game already running')
            return None

        return game

    @commands.command(name='pick', help='Pick member to be on your team', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_pick(self, ctx, member : discord.Member):
        if not self.model.ChkIsReg(ctx):
            return

        choosingId = ctx.message.author.id
        choosingPlayer = ctx.message.author.name
        pickedId = member.id
        pickedPlayer = member.name

        game = await self.can_pick(ctx, choosingId, choosingPlayer, pickedId)
        if not game:
            return
            
        if pickedId not in game.PoolIds():
            await ctx.send(f"{pickedPlayer} not in player pool")
            return

        await self.model.PickPlayer(ctx, game, choosingPlayer, pickedId, pickedPlayer)

    @commands.command(name='sub', help='Sub player due to AFK (player to sub in must be a potential sub via !sub <region>)', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_sub(self, ctx, memSub : discord.Member, memSubWith : discord.Member):
        if not (self.model.ChkIsRegId(memSub.id) and self.model.ChkIsRegId(memSubWith.id)):
            await ctx.send(f'All subbed players must be registered')

        game = await self.can_pick(ctx, memSub.id, memSub.name, memSubWith.id)
        if not game:
            return

        if memSubWith.id in any(self.model.games and self.model.games[reg].IsPlaying(memSub.id) for reg in Region.REGIONS):
            await ctx.send(f"{memSub.name} already in game/player pool")
            return

        if memSubWith.id not in self.model.subs:
            await ctx.send(f"{memSub.name} has not agreed to sub (they can allow themself sub via !sub <region>")
            return

        #must validate memSubWith.id not in another game already but should already be handled with above check

        pSubWith = self.model.playerDB.Find(memSubWith.id, game.region)
        game.Sub(memSub.id, pSubWith)
        await ctx.send(f'{memSub.name} subbed with {memSubWith.name} on {game.region}')
        await self.model.PickPlayer(ctx, game, ctx.member.name, memSubWith.id, memSubWith.name)
    
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
