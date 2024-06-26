# zhex-bot
Discord bot for the arcade game within SC2. It ranks players based on Elo and stores rankings in a database. Players can queue for a game, set team preference, view players' stats and more. The bot is built on Discord.py and uses PostgreSQL as the database.

## Getting started
```
Captain:
  pick        Pick member to be on your team  
  rl          Captain report loss  
  rt          Captain report tie 
  rw          Captain report win 
  sub         Sub player due to AFK (player to sub in must be a potential sub via !sub <region>)

General:  
  add         Add to queue on region (NA/EU/ALL = default); Timeout=60 mins  
  addsub      Allow yourself to be a potential sub on region (captains must already be picking)  
  del         Remove yourself from queue on region (NA/EU/ALL = default)  
  elsub*      Remove yourself as potential sub on region 
  qracepref   Query current race preference for region 
  racepref    Set race preference for region (Z - Zerg, T - Terran, A - All)  
  reg         Register with the server to play private games (registration is required to run all other commands) 
  stats       Retreive stats of player 
  status      Query status of queue and any running games

Type !help command for more info on commands.
```
## Deployment
Bot was setup to be deployed on heroku. Commit the repository to heroku and turn the bot on.

### Unit Testing
- Some unit testing done with pytest.

### Tooling
- Python
- pytest
