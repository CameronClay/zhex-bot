import discord
from discord.ext import commands

class Region:
    NA = 'NA'
    EU = 'EU'
    ALL = 'ALL'
    REGIONS = [NA, EU]
    VALID_REGIONS = [NA, EU, ALL]

    def __init__(self, region):
        self.region = region

    @classmethod
    async def convert(cls, ctx, argument):
        if not argument.upper() in Region.VALID_REGIONS:
            raise commands.ArgumentParsingError(f"Invalid argument; expected {'/'.join(Region.VALID_REGIONS)}")
        
        return cls(argument)

    def Valid(self):
         return self.region in Region.VALID_REGIONS
    
    def ToList(self):
        if self.Valid():
            return Region.REGIONS if self.region == Region.ALL else [self.region]
        return []