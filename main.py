import discord
import json
import requests
import os
import shutil

import vanitybot_descriptions

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
except Exception as e:
    print(f'Uncaught exception ``{e}`` of type ``{type(e)}``')

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)
owner = bot.owner_id


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.id} ({bot.user.name}#{bot.user.discriminator})')
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
    logged_guilds = [x for x in next(os.walk('.'))[1] if x.isnumeric()]
    for guild in logged_guilds:
        if guild not in [guild.id for guild in bot.guilds]:
            shutil.rmtree('./' + guild)


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


@bot.slash_command(name='change_colour',
                   description=vanitybot_descriptions.DESC_COLOUR
                   )
async def change_colour(ctx: discord.ApplicationContext,
                        role: discord.Option(discord.Role, 'Role to be modified', name='role'),
                        value: discord.Option(str, 'Role colour to be set', name='colour')
                        ):
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json') as file:
        data = json.loads(file.read())
    try:
        if not data[str(role.id)] == ctx.interaction.user.id:
            await ctx.respond('You are not this role\'s owner!', ephemeral=True)
            return
    except KeyError:
        await ctx.respond('This role has not (yet) been configured.', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``')
    if len(value) == 6:  # hex
        try:
            await role.edit(colour=discord.Colour.from_rgb(r=int(value[0:2:], 16), g=int(value[3:5:], 16), b=int(value[4:6:], 16)))
            await ctx.respond('Colour changed!', ephemeral=True)
        except discord.errors.Forbidden:
            await ctx.respond(f'This bot is not authorised to change {role}\'s colour!', ephemeral=True)
            return
        except Exception as e:
            await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``')
            return
    else:
        rgb = value.split(' ')
        try:
            for index, val in enumerate(rgb):
                rgb[index] = int(val)
            if len(rgb) != 3: raise ValueError
        except ValueError:
            rgb = value.split(', ')
            try:
                for index, val in enumerate(rgb):
                    rgb[index] = int(val)
                if len(rgb) != 3: raise ValueError
            except ValueError:
                rgb = value.split(',')
                try:
                    for index, val in enumerate(rgb):
                        rgb[index] = int(val)
                    if len(rgb) != 3: raise ValueError
                except ValueError:
                    await ctx.respond('Invalid RGB colour code. Use either hex (without leading #) or RGB separated by `` ``, ``, ``, or ``,``.', ephemeral=True)
        try:
            await role.edit(colour=discord.Colour.from_rgb(r=value[0:2:], g=value[3:5:], b=value[4:6:]))
            await ctx.respond('Colour changed!', ephemeral=True)
            return
        except discord.errors.Forbidden:
            await ctx.respond(f'This bot is not authorised to change {role}\'s colour!', ephemeral=True)
        except Exception as e:
            await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``')
    return


@bot.slash_command(name='change_icon',
                   description=vanitybot_descriptions.DESC_ICON
                   )
async def change_icon(ctx: discord.ApplicationContext,
                      role: discord.Option(discord.Role, 'Role to be modified', name='role'),
                      value: discord.Option(str, 'Emoji or link to image to set role icon to', name='icon')
                      ):
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json') as file:
        data = json.loads(file.read())
    try:
        if not data[str(role.id)] == ctx.interaction.user.id:
            await ctx.respond('You are not this role\'s owner!', ephemeral=True)
            return
    except KeyError:
        await ctx.respond('This role has not (yet) been configured.', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``')
    if value.split('.')[-1].lower() not in ['jpg', 'jpeg', 'png', 'webp'] and (value.startswith('https://cdn.discordapp.com/') or value.startswith('https://media.discordapp.net/'):
        await ctx.respond('Images must be jp(e)g, png, or webp and hosted on Discord.')
        return
    with requests.get(value) as file:
        if len(file.content) > 256000:
            await ctx.respond('Image is too large - role icons must be 256kb or lower.', ephemeral=True)
            return
        try:
            await role.edit(icon=file.content)
            await ctx.respond('Colour changed!', ephemeral=True)
            return
        except discord.errors.Forbidden:
            await ctx.respond(f'This bot is not authorised to change {role}\'s icon!', ephemeral=True)
        except Exception as e:
            await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``')
    return


@bot.slash_command(name='add_role',
                   description=vanitybot_descriptions.DESC_ADDROLE
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
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``')
        return


@bot.slash_command(name='remove_role',
                   description=vanitybot_descriptions.DESC_DELROLE
                   )
async def remove_role(ctx: discord.ApplicationContext,
                      role: discord.Option(discord.Role, 'Role to be added', name='role')
                      ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
    data.pop(data[str(role.id)])
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
