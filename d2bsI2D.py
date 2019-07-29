# ---------------------------
# D2BS: Items 2 Discord
# ---------------------------
# edit your profile.js to enable item logging, example:
#
# Config.ItemInfo = true; // Log stashed, skipped (due to no space) or sold items.
# Config.ItemInfoQuality = [6, 7, 8];
#
# 6, 7, 8 reprensent item quality to be logged to itemlog file
# lowquality = 1
# normal = 2
# superior = 3
# magic = 4
# set = 5
# rare = 6
# unique = 7
# crafted = 8

import json
import requests
import time
import random
import re
import string
	
# discord webhook url
discord_webhook = 'https://discordapp.com/api/webhooks/00000000000000/0000000000000000000000000000000'

# path to itemlog.txt (remember to escape)
# c:\users\bob\ ==> should be ==> c:\\users\\bob\\
itemlog = 'C:\\Users\\bob\\Desktop\\d2bot-with-kolbot-master\\d2bs\\kolbot\\logs\\ItemLog.txt'

# limit of lines in itemlog.txt before we try to empty it
# if this gets too big it might stall your system
itemlog_max_lines = 5000

# sleep time in seconds between each check of itemlog.txt
sleep_between_checks = 30

# item qualities to skip (bot logs cubing stuff etc to the logfile)
skipped_qualities = ['normal', 'magic', 'rare']

# actions to skip
skipped_actions = ['Stashed', 'Sold']

# actions to always post regardless of quality and action
always_actions = ['Kept', 'Cubing Kept', 'Gambled', 'Runeword Kept']

# function for sending messages to discord via webhook
def send_to_discord(message):
	headers = {'Content-Type': 'application/json'}
	data = {}
	data['content'] = message
	payload = json.dumps(data, indent=4)

	r = requests.post(discord_webhook, data=payload, headers=headers)

# function for generating an 'unique ID' for an event (assume no collision)
def generate_event_id(n):
	id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(n))
	return id

# empty the logfile by opening in write-mode and closing again
def empty_logfile():
	try:
		with open(itemlog, "w"):
			return True
	except:
		return False

def main():
	current_line = 0

	while True:
		try:
			with open(itemlog) as f:
				lines = f.readlines()
		except:
			print(f'[FAIL] failed to open itemlog - retrying in {sleep_between_checks} seconds..')
			time.sleep(sleep_between_checks)
			continue

		# first run
		if current_line == 0:
			current_line = len(lines)
			continue

		for idx, line in enumerate(lines):
			if idx >= current_line:

				# try to parse line and extract the info we need
				match = re.search('\[(.+?)\] <(.+?)> <(.+?)> \((.+?)\) (.+?)( \| (.+?)$|$)', line)
				
				if match:
					timestamp = match.group(1)
					character = match.group(2)
					action = match.group(3)
					quality = match.group(4)
					item = match.group(5)
					stats = match.group(6) if len(match.groups()) == 7 else ''
					
					# fix for sold item parsing
					if item.split(' ')[0] == 'Cost:':
						item = match.group(6).split(' | ')[1]					

					# check if quality is to be skipped
					if quality in skipped_qualities and action not in always_actions:
						continue
					
					# check if action is to be skipped
					if action in skipped_actions and action not in always_actions:
						continue

					# format stats for discord
					stats = stats.replace('| ', '\n')

					# create event ID
					event_id = generate_event_id(8)

					# format discord output message
					discord_message = f'character **{character}** performed **{action}** on **{quality.upper()} {item}** /id: **#{event_id}**'

					# add stats to discord output if they are present in the itemlog
					if stats != '':
						discord_message += f'\n`{stats}`'
					
					# finally post info to console and send message to discord
					print('[NEW ITEM]', timestamp, character, quality.upper(), item, '=>', action.upper())

					# skip discord posting if item was part of a recipe
					if not re.search('\{Cubing \d+\}$|\{Cubing-(.+?)\}$', line):
						send_to_discord(discord_message)
				
				else:
					# unable to match line - warn console
					print(f'[WARN] UNABLE TO PARSE: {line}')

		current_line = len(lines)
		
		# clear itemlog file if it has exceeded itemlog_max_lines to avoid it hogging too much resources
		if current_line >= itemlog_max_lines:
			print(f'[WARN] itemlog is {current_line} lines - emptying..')
			if empty_logfile():
				current_line = 0
				print('[OK] itemlog is now empty')
			else:
				print('[FAIL] failed to wipe itemlog!!')

		print(f'[OK] done checking itemlog - sleeping for {sleep_between_checks} seconds..')
		time.sleep(sleep_between_checks)


if __name__ == '__main__':
	print(f'[START] Greetings! :-)')
	print(f'[OK] logfile: {itemlog}')
	print(f'------------')
	main()
