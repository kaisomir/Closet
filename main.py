import discord
import json
import re
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
    quit()
except Exception as e:
    print(f'Uncaught exception ``{e}`` of type ``{type(e)}``')
    quit()

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)
owner = bot.owner_id


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.id} ({bot.user.name}#{bot.user.discriminator})')
    # added to server whilst offline
    for guild in bot.guilds:
        path = f'{filestruct}{guild.id}'
        if not os.path.exists(path):
            os.makedirs(path)
            roles = open(f'{path}/roles.json', 'x+')
            roles.write('{}')
            roles.close()
    # removed from server whilst offline
    logged_guilds = [x for x in next(os.walk('.'))[1] if x.isnumeric()]
    for guild in logged_guilds:
        if guild not in [str(guild.id) for guild in bot.guilds]:
            shutil.rmtree('./' + guild)


@bot.event
async def on_guild_join(guild: discord.Guild):
    path = f'{filestruct}{guild.id}'
    if not os.path.exists(path):
        os.makedirs(path)
        roles = open(f'{path}/roles.json', 'x+')
        roles.write('{}')
        roles.close()


@bot.event
async def on_guild_remove(guild: discord.Guild):
    path = f'{filestruct}{guild.id}'
    if os.path.exists(path):
        shutil.rmtree(path)


@bot.slash_command(name='change_colour',
                   description=vanitybot_descriptions.DESC_COLOUR
                   )
async def change_colour(ctx: discord.ApplicationContext,
                        role: discord.Role = discord.Option(discord.Role, 'Role to be modified', name='role'),
                        value: str = discord.Option(str, 'Role colour to be set', name='colour')
                        ):
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json') as file:
        data = json.loads(file.read())
    try:
        if ctx.interaction.user.id not in data[str(role.id)]['owners']:
            await ctx.respond('You are not authorised to manage this role!', ephemeral=True)
            return
    except KeyError:
        await ctx.respond('This role has not (yet) been configured.', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return
    if not data[str(role.id)]['colour']:
        await ctx.respond('This role\'s colour can\'t be changed.', ephemeral=True)
        return
    if len(value) == 6 and ',' not in value and ' ' not in value:  # hex
        try:
            await role.edit(colour=discord.Colour.from_rgb(r=int(value[0:2:], 16), g=int(value[2:4:], 16), b=int(value[4:6:], 16)))
            await ctx.respond('Colour changed!', ephemeral=True)
        except discord.errors.Forbidden:
            await ctx.respond(f'This bot is not authorised to change {role}\'s colour!', ephemeral=True)
            return
        except Exception as e:
            await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
            return
    else:
        rgb = re.findall(r'\b\d{1,3}\b', value)
        if len(rgb) != 3:
            await ctx.respond('Invalid RGB colour code. Use either hex (without leading #) or RGB separated by `` ``, ``, ``, or ``,``.', ephemeral=True)
            return
        try:
            await role.edit(colour=discord.Colour.from_rgb(r=int(rgb[0]), g=int(rgb[1]), b=int(rgb[2])))
            await ctx.respond('Colour changed!', ephemeral=True)
            return
        except discord.errors.Forbidden:
            await ctx.respond(f'This bot is not authorised to change {role}\'s colour!', ephemeral=True)
            return
        except Exception as e:
            await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
            return


@bot.slash_command(name='change_icon',
                   description=vanitybot_descriptions.DESC_ICON
                   )
async def change_icon(ctx: discord.ApplicationContext,
                      role: discord.Role = discord.Option(discord.Role, 'Role to be modified', name='role'),
                      value: str = discord.Option(str, 'Emoji or link to image to set role icon to', name='icon')
                      ):
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json') as file:
        data = json.loads(file.read())
    try:
        if ctx.interaction.user.id not in data[str(role.id)]['owners']:
            await ctx.respond('You are not authorised to manage this role!', ephemeral=True)
            return
    except KeyError:
        await ctx.respond('This role has not (yet) been configured.', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return
    try:
        await role.edit(unicode_emoji=value)
        await ctx.respond('Icon changed!', ephemeral=True)
        return
    except discord.errors.Forbidden:
        await ctx.respond(f'This bot is not authorised to change {role}\'s icon!', ephemeral=True)
        return
    except discord.errors.HTTPException:
        if not data[str(role.id)]['icon']:
            await ctx.respond('This role\'s icon can\'t be changed.', ephemeral=True)
            return
        if value.startswith('<:'):
            value = bot.get_emoji(int(re.search(r'\d+', value)[0])).url
        if value.split('.')[-1].lower() not in ['jpg', 'jpeg', 'png', 'webp'] and (value.startswith('https://cdn.discordapp.com/') or value.startswith('https://media.discordapp.net/')):
            await ctx.respond('Images must be jp(e)g, png, or webp and hosted on Discord.')
            return
        with requests.get(value) as file:
            if len(file.content) > 256000:
                await ctx.respond('Image is too large - role icons must be 256kb or lower.', ephemeral=True)
                return
            try:
                await role.edit(icon=file.content)
                await ctx.respond('Icon changed!', ephemeral=True)
                return
            except discord.errors.Forbidden:
                await ctx.respond(f'This bot is not authorised to change {role}\'s icon!', ephemeral=True)
                return
            except Exception as e:
                await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
                return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return


@bot.slash_command(name='change_name',
                   description='Change a vanity role\'s name.'
                   )
async def change_name(ctx: discord.ApplicationContext,
                      role: discord.Role = discord.Option(discord.Role, 'Role to change name of.', name='role'),
                      name: str = discord.Option(str, 'Text to set as role name.', name='name')
                      ):
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json') as file:
        data = json.loads(file.read())
    try:
        if ctx.interaction.user.id not in data[str(role.id)]['owners']:
            await ctx.respond('You are not authorised to manage this role!', ephemeral=True)
            return
    except KeyError:
        await ctx.respond('This role has not (yet) been configured.', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return
    if not data[str(role.id)]['name']:
        await ctx.respond('This role\'s name can\'t be changed.', ephemeral=True)
        return
    if len(name) > 100:
        await ctx.respond('Role name must be 100 characters or shorter.')
        return
    try:
        await role.edit(name=name)
        await ctx.respond('Colour changed!', ephemeral=True)
        return
    except discord.errors.Forbidden:
        await ctx.respond(f'This bot is not authorised to change {role}\'s icon!', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return


@bot.slash_command(name='role_permissions',
                   description=vanitybot_descriptions.DESC_ROLEPERMS
                   )
async def role_permissions(ctx: discord.ApplicationContext,
                           role: discord.Role = discord.Option(discord.Role, 'Role to change permissions of.', name='role'),
                           permission: str = discord.Option(str, 'Permission to be changed', name='permission', choices=['colour', 'icon', 'name']),
                           setting: bool = discord.Option(bool, 'Permission allowed or not?', name='setting')
                           ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
    try:
        data[str(role.id)][permission] = setting
        with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'w') as file:
            file.write(json.dumps(data))
        await ctx.respond(f'Role\'s {permission} can now be changed.', ephemeral=True) if setting else await ctx.respond(f'Role\'s {permission} can no longer be changed.', ephemeral=True)
    except KeyError:
        await ctx.respond('This role has not been configured!', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return


@bot.slash_command(name='add_role',
                   description=vanitybot_descriptions.DESC_ADDROLE
                   )
async def add_role(ctx: discord.ApplicationContext,
                   role: discord.Role = discord.Option(discord.Role, 'Role to be added', name='role'),
                   owner: discord.User = discord.Option(discord.User, 'User to whom the role belongs', name='owner')
                   ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
    try:
        data[str(role.id)]
        await ctx.respond('This role has already been configured!')
        return
    except KeyError:
        data[role.id] = {}
        data[role.id]['owners'] = [owner.id]
        data[role.id]['colour'] = True
        data[role.id]['icon'] = True
        data[role.id]['name'] = False
        with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'w') as file:
            file.write(json.dumps(data))
        await ctx.respond('Role configured!', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return


@bot.slash_command(name='add_owner',
                   description=vanitybot_descriptions.DESC_ADDOWNER
                   )
async def add_owner(ctx: discord.ApplicationContext,
                    role: discord.Role = discord.Option(discord.Role, 'Role to add owner to.', name='role'),
                    user: discord.User = discord.Option(discord.User, 'User to add to role.', name='user')
                    ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
    try:
        if user.id not in data[str(role.id)]['owners']:
            data[str(role.id)]['owners'].append(user.id)
            with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'w') as file:
                file.write(json.dumps(data))
            await ctx.respond('User added as owner.', ephemeral=True)
            return
        else:
            await ctx.respond('User is already an owner of this role!', ephemeral=True)
            return
    except KeyError:
        await ctx.respond('This role has not been configured!', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return


@bot.slash_command(name='remove_owner',
                   description=vanitybot_descriptions.DESC_DELOWNER
                   )
async def remove_owner(ctx: discord.ApplicationContext,
                       role: discord.Role = discord.Option(discord.Role, 'Role to remove owner from.', name='role'),
                       user: discord.User = discord.Option(discord.User, 'User to remove from role.', name='user')
                       ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
    try:
        if user.id in data[str(role.id)]['owners']:
            data[str(role.id)]['owners'].remove(user.id)
            with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'w') as file:
                file.write(json.dumps(data))
            await ctx.respond('User removed as owner.', ephemeral=True)
            return
        else:
            await ctx.respond('User is not an owner of this role!', ephemeral=True)
            return
    except KeyError:
        await ctx.respond('This role has not been configured!', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return


@bot.slash_command(name='remove_role',
                   description=vanitybot_descriptions.DESC_DELROLE
                   )
async def remove_role(ctx: discord.ApplicationContext,
                      role: discord.Role = discord.Option(discord.Role, 'Role to be added', name='role')
                      ):
    if not master_perms(ctx, role):
        await ctx.respond('You are not authorised to configure vanity roles!', ephemeral=True)
        return
    with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'r') as file:
        data = json.loads(file.read())
    try:
        data.pop(str(role.id))
        with open(f'{filestruct}{ctx.interaction.guild.id}/roles.json', 'w') as file:
            file.write(json.dumps(data))
        await ctx.respond('Role removed.', ephemeral=True)
        return
    except KeyError:
        await ctx.respond('This role has not been configured!', ephemeral=True)
        return
    except Exception as e:
        await ctx.respond(f'Uncaught exception ``{e}`` of type ``{type(e)}``', ephemeral=True)
        return


def master_perms(ctx: discord.ApplicationContext, role: discord.Role):
    if ctx.interaction.user.guild_permissions.administrator:
        return True
    if (ctx.interaction.user.top_role.position <= role.position):
        return False
    if (ctx.interaction.user.guild_permissions.manage_roles):
        return True
    return False


bot.run(token)
