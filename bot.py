from Model import Model
import Cmd.General
from Cmd.General import General
from Cmd.Captain import Captain
from Cmd.Mod import Mod

from Player import Player
import Region

import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD = os.getenv('DISCORD_GUILD')

    #while True:
    model = Model(TOKEN, GUILD)
    
    Mod(model)
    #model.CreateStubs(Region.NA, 2)
    with model:
        model.bot.add_cog(model)
        model.bot.add_cog(General(model))
        model.bot.add_cog(Captain(model))
        model.bot.add_cog(Mod(model))
        model.run()