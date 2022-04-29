import discord
import json

try:
    with open('config.json', 'r') as file:
        data = json.loads(file.read())
except FileNotFoundError:
    print('File does not exist. Please copy example.json to config.json and edit the variables to match.')
    quit()

for entry in data:
    if not data[entry]:
        print(f'{entry} must be filled.')
        quit()

