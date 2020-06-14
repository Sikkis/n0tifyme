#!/usr/bin/env python3
import time
import os
import json
import sched
from itertools import islice
import sys, signal, getopt
import pymsteams
import configparser

s = sched.scheduler(time.time, time.sleep)
terminate=False
teamsHook = None
#Default time
t = 10

#################################################
#                   COLORS                      #
#################################################
note = "\033[0;0;33m[-]\033[0m"
warn = "\033[0;0;31m[!]\033[0m"
info = "\033[0;0;36m[i]\033[0m"
question = "\033[0;0;37m[?]\033[0m"
debug = "\033[0;0;31m[DEBUG]\033[0m"
success = "\033[0;0;92m[+]\033[0m"


def initialization(rules):
    global warn
    remove_wrong_rules = []
    for rule in rules:
        try:
            thefilepath = rules[rule]["filename"]
            count = len(open(thefilepath).readlines())
            rules[rule]["count"] = count            
        except:
            print(warn+ " Filepath "+rules[rule]['filename']+" for "+ rule +" does not exists. It will be removed from monitoring.")
            remove_wrong_rules.append(rule)    

    for i in range(0, len(remove_wrong_rules)):
        del rules[remove_wrong_rules[i]]
    
    return rules

def run_rules(a='default'):
    for rule in rules:    
        count = len(open(rules[rule]["filename"]).readlines())
        if count != rules[rule]["count"]:
            with open(rules[rule]["filename"]) as lines:
                for line in islice(lines, rules[rule]["count"]-1, count-1):
                    if rules[rule]["condition"] in line:
                        print(info +" " + rules[rule]['alert'] + " from:\033[0;0;36m"+line + "\033[0m")
                        send_new_message_teams(rules[rule],line)
                        rules[rule]["count"] = count

def loop(rules):
    global t
    s.enter(t,1,run_rules)
    s.run()

def signal_handling(signum,frame):           
    global terminate                         
    terminate = True                         

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"ht:",["time="])
    except getopt.GetoptError:
        print('./n0tifYme.py -t <time>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('./n0tifYme.py -t <time>')
            sys.exit()
        elif opt in ("-t", "--time"):
            global t
            t = int(arg)

def send_new_message_teams(rule,message):
    """Send a Microsoft Teams Activity Card HTTP POST message to a web hook"""
    global teamsHook
    myTeamsMessage = pymsteams.connectorcard(teamsHook)
    myTeamsMessage.title("[+] New "+ rule['type'])

    # create the section
    myMessageSection = pymsteams.cardsection() 
    myTeamsMessage.text(rule['alert'])
    myMessageSection.activityTitle("Information")
    myMessageSection.activitySubtitle(message)
    myTeamsMessage.addSection(myMessageSection)
    
    #send notification to Microsoft Teams
    if (myTeamsMessage.send()):
        print(success + " New message successfully posted to Microsoft Teams")
    else:
        print(warn  + " Message was not posted to Microsoft Teams.")


if __name__ == '__main__':
    main(sys.argv[1:])    
    signal.signal(signal.SIGINT,signal_handling) 
    
    # Read Rule JSON File
    if  os.path.exists("rules.json"):
        with open('rules.json', 'r') as filehandle:
            rules = json.load(filehandle)
        rules = initialization(rules)

    # Read bot configuration
    if  os.path.exists("bot.conf"):
        config = configparser.ConfigParser()
        config.read('bot.conf')

        if config.has_section("teams"):
            if config.has_option("teams","teamsHook"):
                teamsHook = config['teams']['teamsHook']
            else:
                print(info + "Microsoft Teams Web Hook was not provided")
                sys.exit(0)

    
    # Start the monitoring
    print(note + " n0tifYme has started monitoring your rules..")
    while (True):
        loop(rules)
        if terminate:
            print(warn + " Terminating...")
            break
