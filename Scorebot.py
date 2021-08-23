import os
import discord
import pandas as pd
import re
import numpy as np
from replit import db
from discord.ext import commands
from keep_alive import keep_alive

activity = discord.Game(name="with the lives of insignificant mortals")

bot = commands.Bot(command_prefix='!', help_command=None, activity=activity)
adminrole = 'SpellBot Admin'
spellbot = 725510263251402832

my_secret = os.environ['Token3']

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


def listconv(args:list):
  points = 0
  for i in args:
    points += int(db['points'].get(i))
  return points

async def msg_parser(ctx, message):
    keys = list(db['points'].keys())
    message = re.split('\r|\n', message)
    for num, i in enumerate(message):
        message[num] = re.split("-", i)
    df = pd.DataFrame(message, columns=['College', 'User', 'Colors', 'Points'])
    #for i, user in enumerate(df['User']):
    #  userid = 
    #  userprof = await ctx.guild.fetch_member(userid)
    #  df['User'][i] = str(userprof.mention)
    dfmask = df['College'] == '!gamereport '
    df['reference'] = df['User'] * dfmask
    df.loc[df.reference == '', 'reference'] = np.nan
    df['reference'] = df['reference'].ffill()
    df = df[~dfmask]
    #df= df.tail(4)
    df['Test'] = df['Points'].str.findall('(' + '|'.join(keys) + ')')
    df['total_points'] = df['Test'].apply(listconv)
    df.drop(['Test'], axis=1, inplace=True)
    return df

pd.set_option('max_columns', None)
# Commands for reporting, editing, exporting, and resetting season scores
@bot.command()
async def gamereport(ctx):
    if ctx.author == bot.user:
        return
    content = ctx.message.content
    df = await msg_parser(ctx, content)
    embedtitle = 'Game ' + str(df['reference'][1]) + ' successfully recorded'
    value = ""
    reportembed = discord.Embed(description=embedtitle ,color=15277667)
    for i in range(len(df['User'])):
      name = list(df['User'])
      points = list(df["total_points"])
      value += str(name[i]) + ': ' + str(points[i])
      if i == 1:
        value += ',\r'
      elif i != 4:
        value += ', '
    reportembed.add_field(name='Points earned',value=value)
      #inline = False if i == 1 else True
      #reportembed.add_field(name=str(name[i]), value=str(points[i]), inline=inline)
    print(df)
    if os.path.exists('scores.csv'):
      df.to_csv('scores.csv', mode='a', index=False, header=False)
    else:
      df.to_csv('scores.csv', mode='w', index=False)
    await ctx.channel.send(embed=reportembed)
    pass

@bot.command()
@commands.has_role(adminrole)
async def editscore(ctx, user:commands.UserConverter, points:int):
  userpost = str(user.name) + '#' + str(user.discriminator)
  Edit = ['', userpost, '', 'edited', ctx.author.name, points]
  df = pd.DataFrame(Edit).T
  if os.path.exists('scores.csv'):
    df.to_csv('scores.csv', mode='a', index=False, header=False)
  else:
    df.to_csv('scores.csv', mode='w', index=False)
  msg = str(points) + ' points awarded to ' + str(user.name)
  await ctx.channel.send(msg)
  pass

@editscore.error
async def editscore_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

@bot.command()
@commands.has_role(adminrole)
async def scores(ctx):
  if os.path.exists('scores.csv'):
    df = pd.read_csv('scores.csv')
    df['games'] = np.where(df['Points']=='edited', 0, 1)
    df.drop(['College', 'Colors', 'Points', 'reference'], axis=1, inplace=True)
    df = df.groupby(df['User']).sum()
    df.columns = ['total_points', 'games']
    df['points per game'] = df['total_points']/df['games']
    df.to_csv('totals.csv')
    await ctx.author.send(file=discord.File('./scores.csv'))
    await ctx.author.send(file=discord.File('./totals.csv'))
  else:
    await ctx.author.send('There are currently no score files')
  pass

@scores.error
async def scores_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

@bot.command()
@commands.has_role(adminrole)
async def resetscores(ctx):
  if os.path.exists('scores.csv'):
    if os.path.exists('scores.bak'):
      os.remove('scores.bak')
    os.rename('scores.csv', 'scores.bak')
  if os.path.exists('totals.csv'):
    if os.path.exists('totals.bak'):
      os.remove('totals.bak')
    os.rename('totals.csv', 'totals.bak')
  await ctx.channel.send('__**Karn has started a new season. All scores have been reset.**__')  
  pass

@resetscores.error
async def resetscores_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

# Commands for editing the point codes and values used in the message parser.
def add_award(award, amount):
  if 'points' in db.keys():
    db['points'][award] = amount
  else:
    db['points'] = {award:amount}
    return award + ' succesfully added'


def del_award(award):
    keys = db['points'].keys()
    if award in db['points'].keys():
        del db['points'][award]
        return award + ' deleted'
    else:
        return award + ' not found.\r' + 'Current points: ' + str(list(keys))[1:-1]

@bot.command()
@commands.has_role(adminrole)
async def pointlist(ctx):
  keys = db['points'].keys()
  message = 'Current points: ' + str(list(keys))[1:-1]
  await ctx.channel.send(message)
  pass

@pointlist.error
async def pointlist_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

@bot.command()
@commands.has_role(adminrole)
async def addpoint(ctx, award, amount):
    add_award(award=award, amount=amount)
    send = award + ' successfully added'
    await ctx.channel.send(send)
    pass

@addpoint.error
async def addpoint_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass


@bot.command()
@commands.has_role(adminrole)
async def delpoint(ctx, award):
    await ctx.channel.send(del_award(award=award))
    pass

@delpoint.error
async def delpoint_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

@bot.command()
@commands.has_role(adminrole)
async def clrpoint(ctx):
    db['points'].clear()
    await ctx.channel.send('All points successfully cleared')
    pass

@clrpoint.error
async def clrpoint_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

# Commands for editing the list of roles included in the !result function.
@bot.command()
@commands.has_role(adminrole)
async def rolelist(ctx):
  roles = str(list(db['roles']))[1:-1]
  message = 'Current roles: ' + str(roles)
  await ctx.channel.send(message)
  pass

@rolelist.error
async def rolelist_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

@bot.command()
@commands.has_role(adminrole)
async def addrole(ctx, role):
  if 'roles' in db.keys():
    db['roles'].append(role)
  else:
    db['roles'] = [role]
  send = 'Role ' + role + ' successfully added.'
  await ctx.channel.send(send)
  pass

@addrole.error
async def addrole_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

@bot.command()
@commands.has_role(adminrole)
async def delrole(ctx, role):
  db.roles.remove(role)
  send = 'Role ' + role + ' successfully deleted.'
  await ctx.channel.send(send)
  pass

@delrole.error
async def delrole_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

@bot.command()
@commands.has_role(adminrole)
async def clrrole(ctx):
  db.roles.clear()
  await ctx.channel.send('All roles successfully cleared')
  pass

@clrrole.error
async def clrrole_error(ctx, error):
  if isinstance(error, commands.MissingRole):  
    message = await ctx.channel.send('You do not have permission to use this command.')
    await message.delete(delay=10)
  pass

helpembed=discord.Embed(description="**Scorebot Help**",color=15277667)
#helpembed.set_author(name="Scorebot Help")
helpembed.add_field(name="`scorehelp`", value="Displays this message", inline=False)
helpembed.add_field(name="`result <Spellbot Reference>`", value="DMs the user a template to report the results of your game. Use in the same channel as the original SpellBot Post", inline=False)
helpembed.add_field(name="`gamereport`", value="Report the results of a game. **This command is automatically created in the correct format with the `!result` command. Please do not use without that template.**", inline=False)
#helpadmin = helpembed
helpadmin=discord.Embed(description="**Scorebot Help**",color=15277667)
#helpembed.set_author(name="Scorebot Help")
helpadmin.add_field(name="`scorehelp`", value="Displays this message", inline=False)
helpadmin.add_field(name="`result <Spellbot Reference>`", value="DMs the user a template to report the results of your game", inline=False)
helpadmin.add_field(name="`gamereport`", value="Report the results of a game. **This command is automatically created in the correct format with the `!result` command. Please do not use without that template.**", inline=False)
helpadmin.add_field(name = chr(173), value = chr(173))
helpadmin.add_field(name="*The following commands are admin only commands.*", value="\u200b", inline=False)
helpadmin.add_field(name="`pointlist`", value="Lists all current point codes", inline=False)
helpadmin.add_field(name="`addpoint <code> <value>`", value="Adds a point that is available to earn. The code is what will be used by players in the report.", inline=False)
helpadmin.add_field(name="`delpoint <code>`", value="Deletes the specified point from the list of possible points.", inline=False)
helpadmin.add_field(name="`clrpoint`", value="Clears the list of all possible points.", inline=False)
helpadmin.add_field(name="`rolelist`", value="Lists all roles currently checked for by the bot.", inline=False)
helpadmin.add_field(name="`addrole <role name>`", value="Adds a new role to the list of roles checked for by the bot.", inline=False)
helpadmin.add_field(name="`delrole <role name>`", value="Deletes the specified role from the list of roles checked for by the bot.", inline=False)
helpadmin.add_field(name="`clrrole`", value="Clears the list of all roles checked for by the bot.", inline=False)
helpadmin.add_field(name="`editscore <user> <value>`", value="Used to manually edit the score of a particular user. Value may be negative to remove points from a user as well.", inline=False)
helpadmin.add_field(name="`scores`", value="DMs the user the score files. The first file is the game by game breakdown and the second is the totals for the season.", inline=False)
helpadmin.add_field(name="`resetscores`", value="Resets the scores for the current season. ***This will delete the files for the scores. make sure you have a copy first as this cannot be undone!***", inline=False)

@bot.command()
@commands.has_role(adminrole)
async def scorehelp(ctx):
  await ctx.author.send(embed=helpadmin)
  pass

@scorehelp.error
async def scorehelp_error(ctx, error):
  if isinstance(error, commands.MissingRole):
    await ctx.author.send(embed=helpembed)
  pass

# Embed for instructions on reporting
embedreport_body1 = 'You can use the template in the following message and instructions below to report the points for your game. **Please make sure to leave the dashes when editing the template.**\r\r'
embedreport_body2 = '  • Copy the template in the following message and replace "WUBRG" with the colors each player was playing.\r'
embedreport_body3 = '  • Replace "Points" with the codes for the points each player earned during the game. A list of available points with the associated codes can be found at <#822634727273136178>.\r'
embedreport_body4 = '  • Take your completed template and post it in the ***PLACEHOLDER*** channel. Don\'t forget to attach a screenshot of your completed game with each player\'s life total set to the number of points they earned for the game.\r\r'
embedreport_body5 = 'Once your scores have been updated, you will see a post from Scorebot confirming your submission.'
embedreport=discord.Embed(description=embedreport_body1 + "\u200b" + embedreport_body2 + "\u200b" + embedreport_body3 + "\u200b" + embedreport_body4 + embedreport_body5, color=15277667)
embedreport.set_author(name="Report A Game")

# Command to send the user a template for reporting the game with the reference number "findme"
@bot.command()
async def result(ctx, findme):
    channel = ctx.channel
    async for message in channel.history(limit=500):
        if message.embeds != []:
            embed = (message.embeds[0])
            embed_footer = embed.footer.text
            if findme in embed_footer:
                plyrlist = embed.fields[1].value              
                printroles = ''
                msgtxt = '!gamereport -' + embed_footer + '\r'
                if ',' in plyrlist:
                  players = re.split(', ',plyrlist)
                else:
                  players = [plyrlist]
                print(players[0])
                for i, plyr in enumerate(players):
                    userid = players[i][2:-1]
                    print(userid)
                    userprof = await ctx.guild.fetch_member(userid)
                    user = str(userprof.name) + '#' + str(userprof.discriminator)
                    roles = userprof.roles
                    for i, role in enumerate(roles):
                      if roles[i].name in db['roles']:
                        printroles += str(roles[i].name) + ','
                    if printroles == '':
                      printroles = 'No valid roles'
                    msgtxt += printroles[:-1] + '-' + user + '-WUBRG-Points\r'
                    printroles = ''
                break
                msgtxt = msgtxt[:-2]  
    await ctx.author.send(embed=embedreport)  
    await ctx.author.send(msgtxt)
    pass

@bot.command()
async def test(ctx, id:int):
  user = bot.get_user(id)
  print(user)

keep_alive()
bot.run(my_secret)

