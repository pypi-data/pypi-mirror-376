#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import argparse
import requests
import time

import pprint

from w3lib.url import safe_url_string
import validators

# Globals
VERSION = '1.2'

CRDF_API_BASE_URL = 'https://threatcenter.crdf.fr/api/v1/'
CRDF_API_KEY = 'SECRET_CRDF_API_KEY'

# Options definition
parser = argparse.ArgumentParser(description="version: " + VERSION)
parser.add_argument('-k', '--api-key', help='API key (could either be provided in the "%s" env var)' % CRDF_API_KEY, type = str)
parser.add_argument('-i', '--input-file', help='Input file (either list of newline-separated FQDN, or a list newline-separated of CRDF refs)')
parser.add_argument('-a', '--action', help = 'Action to do on CRDF (default \'submit\')', choices = ['submit', 'check', 'info_key'], type=str.lower, default = 'submit')

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def crdf_info_key(options):
    retval = os.EX_OK
    url_endpoint = CRDF_API_BASE_URL + 'info_key.json'
    #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}
    
    req_data = { "token": options.api_key,
                 "method": "info_key" }
                 
    req = requests.post(url_endpoint, json=req_data)
    if req.ok:
        req_json = req.json()
        if req_json.get('error') == False:
            print("[+] CRDF check request successful")
            pprint.pprint(req_json)
    else:
        print("[!] error while checking info about the CRDF API key")
        pprint.pprint(req.status_code)
        print(req.content)
    print('-------------------')
    
    return retval



def crdf_check(options):
    retval = os.EX_OK
    
    url_endpoint = CRDF_API_BASE_URL + 'submit_get_info.json'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'}

    refs = []
    
    if os.path.isfile(options.input_file):
        with open(options.input_file, mode='r', encoding='utf-8') as fd_input:
            refs = fd_input.read().splitlines()
        
        if refs:
            #pprint.pprint(refs)
            
            for ref in refs:
                ref = ref.strip()
                req_data = { "token": options.api_key,
                             "method": "submit_get_info",
                             "ref": ref}
                req = requests.post(url_endpoint, headers=headers, json=req_data)
                print("[+] CRDF ref '%s'" % ref)
                
                if req.ok:
                    req_json = req.json()
                    if req_json.get('error') == False:
                        print("[+] CRDF check request successful")
                        pprint.pprint(req_json)
                else:
                    print("[!] error while checking CRDF ref")
                    pprint.pprint(req.status_code)
                
                print('-------------------')
                
        else:
            retval = os.EX_NOINPUT
    
    else:
        retval = os.EX_NOINPUT
        
    return retval

def crdf_submit(options):
    retval = os.EX_OK
    
    url_endpoint = CRDF_API_BASE_URL + 'submit_url.json'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}
    
    malicious_url = []
    
    if os.path.isfile(options.input_file):
        with open(options.input_file, mode='r', encoding='utf-8') as fd_input:
            for line in fd_input:
                line = line.strip()
                if line.startswith(('http://', 'https://')):
                    entry = safe_url_string(line)
                    if validators.url(entry):
                        malicious_url.append(entry)
                else:
                    entry_http = safe_url_string('http://'+line)
                    if validators.url(entry_http):
                        malicious_url.append(entry_http)
                    
                    entry_https = safe_url_string('https://'+line)
                    if validators.url(entry_https):
                        malicious_url.append(entry_https)
        
        if malicious_url:
            #pprint.pprint(malicious_url)
            
            # slices of max 1000 url
            for sublist in chunks(malicious_url, 1000):
                req_data = { "token": options.api_key,
                             "method": "submit_url",
                             "urls": sublist }
                req = requests.post(url_endpoint, headers=headers, json=req_data)
                
                if req.ok:
                    req_json = req.json()
                    if req_json.get('error') == False:
                        print("[+] CRDF submit request successful")
                        pprint.pprint(req_json)
                
                else:
                    print("[!] error while submitting CRDF URLs")
                    pprint.pprint(req.status_code)
                    print(req.content)
                
                print('-------------------')
                
                # 2 submissions per minute
                time.sleep(31)
            
    else:
        retval = os.EX_NOINPUT
        
    return retval

def main():
    global parser
    options = parser.parse_args()
    
    api_key = options.api_key
    if not(api_key):
        if CRDF_API_KEY in os.environ:
            api_key = os.environ[CRDF_API_KEY]
        else:
            parser.error('[!] No API key has been provided, exiting.')
    options.api_key = api_key
    
    
    if (options.input_file == None) and (options.action != 'info_key'):
         parser.error('Please specify a valid input file or a valid URL')
    
    if options.action == 'submit':
        sys.exit(crdf_submit(options))
    
    elif options.action == 'check':
        sys.exit(crdf_check(options))
        
    elif options.action == 'info_key':
        sys.exit(crdf_info_key(options))

if __name__ == "__main__" :
    main()