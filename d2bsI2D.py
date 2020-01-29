import argparse
import configparser
import json
import os
import requests
import sys
import time
import re


# function for sending messages to discord via webhook
def send_to_discord(indata, file=False):
    
    if file:
        headers = {'Content-Type': 'multipart/form-data'}
        with open(indata, 'rb') as f:
            payload = {f'_{indata}': (indata, f.read())}

        message2 = {'content': 'yass eee'}
        r = requests.post(discord_webhook, files=payload, data=message2)
        
    else:
        headers = {'Content-Type': 'application/json'}
        data = {'content': indata}
        payload = json.dumps(data, indent=4)
        r = requests.post(discord_webhook, data=payload, headers=headers)
    
    if ['200', '204'] in r.status_code:
        print(f'[OK] discord webhook success -> {r.status_code}')
    else:
        print(f"[FAIL] discord webhook failed: {r.content.decode('utf-8')}")

# empty the logfile by opening in write-mode and closing again
def empty_logfile():
    try:
        with open(file_itemlog, "w"):
            return True
    except:
        return False

# will try to get lastArea from the profile json
def get_last_area(character):
    try:
        character_json = os.path.join(dir_kolbotdata, character + '.json')
        with open(character_json) as f:
            data = json.load(f)
            return data['lastArea']
    except:
        return 'Unknown Area'

def main():
    current_line = 0

    while True:
        try:
            with open(file_itemlog) as f:
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

                match = re.search('\[(.+?)\] <(.+?)> <(.+?)> \((.+?)\) (.+?)( \| (.+?)$|$)', line)

                if match:
                    timestamp = match.group(1)
                    character = match.group(2)
                    action = match.group(3)
                    quality = match.group(4)
                    item = match.group(5)
                    stats = match.group(6) if len(match.groups()) == 7 else ''
                    area = get_last_area(character)

                    # fix for sold item parsing
                    if item.split(' ')[0] == 'Cost:':
                        item = match.group(6).split(' | ')[1]                   

                    # check if action is to be skipped
                    if action not in always_actions:
                        continue

                    # format stats for discord
                    stats = stats.replace('| ', '\n')

                    # format discord output message
                    discord_message = f'[{character}] with **{action}** on **{quality.upper()} {item}** from **{area}**'

                    # add stats to discord output if they are present in the itemlog
                    if stats != '':
                        discord_message += f'\n`{stats}`'
                    
                    # finally post info to console and send message to discord
                    print('[NEW ITEM]', timestamp, character, area, quality.upper(), item, '=>', action.upper())

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
    #main()

    # get config file
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='configfile (default: config.ini)', default='config.ini')

    config_file = parser.parse_args().config

    if not os.path.isfile(config_file):
        print(f'!!! CONFIG FILE NOT FOUND: {config_file}')
        sys.exit(0)

    # read config file
    cf = configparser.ConfigParser()
    cf.read(config_file)

    dir_kolbot = os.path.join(cf.get('paths', 'kolbot'))
    dir_kolbotdata = os.path.join(cf.get('paths', 'kolbot'), 'd2bs', 'kolbot', 'data')

    dir_kolbotimages = os.path.join(cf.get('paths', 'kolbot'), 'images')
    
    file_itemlog = os.path.join(dir_kolbot, 'd2bs', 'kolbot', 'logs', 'ItemLog.txt')

    sleep_between_checks = int(cf.get('text', 'sleep_between_checks'))
    
    itemlog_max_lines = int(cf.get('text', 'itemlog_max_lines'))
    
    always_actions = cf.get('text', 'always_actions')
    
    discord_webhook = cf.get('general', 'discord_webhook')
    
    print(f'[!] Greetings! :-)')
    
    if not os.path.isdir(dir_kolbot):
        print(f'[-] MISSING DIRECTORY -> Kolbot: {dir_kolbot}')
        sys.exit()
    else:
        print(f'[+] DIRECTORY -> Kolbot: {dir_kolbot}')
    
    if not os.path.isdir(dir_kolbotdata):
        print(f'[-] MISSING DIRECTORY -> Data: {dir_kolbotdata}')
        sys.exit()
    else:
        print(f'[+] DIRECTORY -> Data: {dir_kolbotdata}')
    
    if not os.path.isdir(dir_kolbotimages):
        print(f'[-] MISSING DIRECTORY -> Images: {dir_kolbotimages}')
        sys.exit()
    else:
        print(f'[+] DIRECTORY -> Images: {dir_kolbotimages}')
    
    if not os.path.isfile(file_itemlog):
        print(f'[-] MISSING FILE -> ItemLog.txt: {file_itemlog}')
        sys.exit()
    else:
        print(f'[+] FILE -> ItemLog.txt: {file_itemlog}')
    
    print(f'[+] TEXT SETTING -> ENABLED: {itemlog_max_lines}')
    print(f'[+] TEXT SETTING -> itemlog_max_lines: {itemlog_max_lines}')
    print(f'[+] TEXT SETTING -> sleep_between_checks: {sleep_between_checks}')
    print(f'[+] TEXT SETTING -> always_actions: {always_actions}')

    print(f'[+] IMAGE SETTING -> ENABLED: {itemlog_max_lines}')
    print(f'[+] IMAGE SETTING -> itemlog_max_lines: {itemlog_max_lines}')
    print(f'------------')

    # create logs directory
    #pathlib.Path(logs_dir).mkdir(parents=True, exist_ok=True)