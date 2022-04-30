import discord
import json
import responses
import os
import shutil

try:
    with open('config.json', 'r') as file:
        data = json.loads(file.read())
    token = data['token']
    filestruct = data['filestruct']
except FileNotFoundError:
    print('File does not exist. Please copy example.json to config.json and edit the variables to match.')
    quit()
except KeyError as e:
    print(f'The required variable {e} has an invalid name.')

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)
owner = bot.owner_id


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.id} ({bot.user.name}#{bot.user.discriminator})')
    print([guild.id for guild in bot.guilds])
    for guild in bot.guilds:
        path = f'{filestruct}{guild.id}'
        if not os.path.exists(path):
            os.makedirs(path)
            roles = open(f'{path}/roles.json', 'x+')
            roles.write('{}')
            roles.close()
            masters = open(f'{path}/masters.json', 'x+')
            roles.write('{}')
            masters.close()


@bot.event
async def on_guild_join(guild: discord.Guild):
    path = f'{filestruct}{guild.id}'
    if not os.path.exists(path):
        os.makedirs(path)
        roles = open(f'{path}/roles.json', 'x+')
        roles.write('{}')
        roles.close()
        masters = open(f'{path}/masters.json', 'x+')
        masters.write('{}')
        masters.close()


@bot.event
async def on_guild_remove(guild: discord.Guild):
    path = f'{filestruct}{guild.id}'
    if os.path.exists(path):
        shutil.rmtree(path)


@bot.slash_command(name='modify',
                   description=responses.DESC_MODIFY,
                   guild_ids=[guild.id for guild in bot.guilds]
                   )
async def modify(ctx: discord.ApplicationContext,
                 role: discord.Option(discord.Role, 'Role to be modified', name='role'),
                 property: discord.Option(str, 'Property to modify', name='property', choices=['icon', 'colour'])
                 ):
    guild = ctx.interaction.guild
    with open(f'{filestruct}{guild.id}/roles.json') as file:
        data = json.loads(file.read())
    return


@bot.slash_command(name='add_role',
                   description=responses.DESC_ADDROLE,
                   guild_ids=[guild.id for guild in bot.guilds]
                   )
async def add_role(ctx: discord.ApplicationContext,
                   role: discord.Option(discord.Role, 'Role to be added', name='role'),
                   owner: discord.Option(discord.User, 'User to whom the role belongs', name='owner')
                   ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
        print(data)
    try:
        data[str(role.id)]
        await ctx.respond('This role has already been configured!')
        return
    except KeyError:
        data[role.id] = owner.id
        with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'w') as file:
            file.write(json.dumps(data))
        await ctx.respond('Role configured!')
        return


@bot.slash_command(name='remove_role',
                   description=responses.DESC_DELROLE,
                   guild_ids=[guild.id for guild in bot.guilds]
                   )
async def remove_role(ctx: discord.ApplicationContext,
                      role: discord.Option(discord.Role, 'Role to be added', name='role')
                      ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
    data.pop(data[role.id])
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'w') as file:
        file.write(json.dumps(data))


def master_perms(ctx: discord.ApplicationContext, role: discord.Role):
    if ctx.interaction.user.guild_permissions.administrator:
        return True
    if (ctx.interaction.user.top_role.position <= role.position):
        return False
    if (ctx.interaction.user.guild_permissions.manage_roles):
        return True
    with open(f'{filestruct}{ctx.interaction.guild.id}/masters.json', 'r') as file:
        masters = json.loads(file.read())
    for role in ctx.interaction.user.roles:
        if role.id in masters:
            return True
    return False


bot.run(token)
