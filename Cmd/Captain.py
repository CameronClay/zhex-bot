from discord.ext import commands
from Model import Model
import itertools
import discord

from Game import State
from Player import MatchRes
from Region import Region

from Utility import CodeB, CodeSB

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
            await ctx.send(CodeSB(f'Must be a captain in order to pick'))
            return None

        if choosingId == pickedId:
            await ctx.send(CodeSB(f'Cannot pick self'))
            return None

        return self.model.games[region]

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

        if game.playerTurn.id != choosingId:
            await ctx.send(CodeSB(f'Not your turn to pick'))
            return None
            
        if pickedId not in game.PoolIds:
            await ctx.send(CodeSB(f"{pickedPlayer} not in player pool"))
            return    
        
        if game.state == State.IN_GAME:
            await ctx.send(CodeSB(f'Game already running'))
            return None

        await self.model.PickPlayer(ctx, game, choosingPlayer, pickedId, pickedPlayer)

    @commands.command(name='sub', help='Sub player due to AFK (player to sub in must be a potential sub via !sub <region>)', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_sub(self, ctx, memSub : discord.Member, memSubWith : discord.Member):
        if not (self.model.ChkIsRegId(memSub.id) and self.model.ChkIsRegId(memSubWith.id)):
            await ctx.send(f'`All subbed players must be registered`')

        choosingId = ctx.message.author.id
        choosingPlayer = ctx.message.author.name

        game = await self.can_pick(ctx, choosingId, choosingPlayer, memSubWith.id)
        if not game:
            return

        if any(self.model.games[reg] and self.model.games[reg].IsPlaying(memSubWith.id) for reg in Region.REGIONS):
            await ctx.send(f"`{memSubWith.name} already in game/player pool`")
            return

        if memSubWith.id not in self.model.subs[game.region]:
            await ctx.send(CodeSB(f"{memSubWith.name} has not agreed to sub (they can allow themself sub via !sub <region>"))
            return

        #must validate memSubWith.id not in another game already but should already be handled with above check

        pSubWith = self.model.playerDB.Find(memSubWith.id, game.region)
        game.Sub(memSub.id, pSubWith)
        await ctx.send(f'`{memSub.name} subbed with {memSubWith.name} on {game.region}`')
        if game.state != State.IN_GAME:
            await self.model.PickPlayer(ctx, game, choosingPlayer, memSubWith.id, memSubWith.name)
    
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
