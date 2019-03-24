#!/usr/bin/env python3

import os
import sys
import re
import json
import argparse
import subprocess

from collections import defaultdict


# default directory path containing CVE json
CVE_DETAIL_PATH = 'cvelist'
CVE_PATCH_PATH = 'cve_patch_url.json'
CVE_TARGET_COMMIT_ISSUE = 'cve_target_commit_issue.json'
CVEDIR_COMMIT_PATH = 'cvedir_commit.json'

# config
cve_dir_list = []
cve_json_list = []
patch_url = {}

tmp_cveid = ''
cve_commit = defaultdict(list)
commit_find = 0
rest_cve = []

class Config_OBJ:
	def __init__(self, **entries):
		self.__dict__.update(entries)


def init_cfg(args):
    cfg = {}
    if args.cvedir:
        if os.path.exists(args.cvedir):
            cfg["cve_abs_dir"] = os.path.abspath(args.cvedir)
            if args.cvedir_commit:
                cfg['cvedir_commit'] = True
        else:
            print("Error: directory {} not found".format(args.cvedir))
            sys.exit(1)
    elif args.patch:
        cfg["patch"] = args.patch
    elif args.target_json:
        cfg["target_json"] = args.target_json    
    elif args.circl:
        cfg['circl'] = True
        print("Search CIRCL database online")
    elif args.task:
        cfg['task'] = args.task
    elif args.cveid:
        cfg["cveid"] = args.cveid
    else:
        print("Error: there are no cve json specified")
        sys.exit(1) 


    # in order to use cfg like cfg.cve_abs_dir
    cfg = Config_OBJ(**cfg)
    return cfg

def init_arg(argv):
    parser = argparse.ArgumentParser(prog='cvepatch', description='CVE Patch Search Tool')
    parser.add_argument('-d', '--cvedir', help='json files directory containing CVE details', \
            type=str, required=False)
    parser.add_argument('-p', '--patch', help='formatted json files containing CVE patch url', \
            type=str, required=False)
    parser.add_argument('-c', '--`cveid`', help='search CVE patch url' \
            "cveid format: CVE-20XX-XXXX", type=str, required=False)
    # parser.add_argument('-v', '--product', help='search CVE info about the product')
    parser.add_argument('-ts', '--target_json', help='given the json and print related commit url')
    parser.add_argument('-ci', '--circl', help='search CIRCL CVE database online', action='store_true', required=False)
    parser.add_argument('-dc', '--cvedir_commit', help='search CVE dir commit', action='store_true', required=False)
    parser.add_argument('-t', '--task', help='task for lulu', type=str, required=False)
    args = parser.parse_args()

    if len(argv) < 3:
        parser.print_help()
        sys.exit(1)
    cfg = init_cfg(args)
    return cfg

def load_cve_dir(cve_abs_dir):
    re_findpatch = re.compile(r'((http|ftp|https)://).*?(\.patch|\.diff).*?')
    for root, dirs, files in os.walk(cve_abs_dir):
        for cve_json in files:
            # collect CVE json
            cve_json_name = os.path.splitext(cve_json)[0]
            cve_json_ext = os.path.splitext(cve_json)[1]
            if cve_json_ext == '.json':
                datas = open(os.path.join(root, cve_json), encoding='utf-8')
                data = json.load(datas)
                if "references" in data.keys():
                    if "reference_data" in data["references"].keys():
                        url = data["references"]["reference_data"][0]["url"]
                        result = re_findpatch.search(url)
                        if result is not None:
                            patch_url[cve_json_name] = result.group()
    length = len(patch_url)
    if length == 0:
        print("failed to load CVE dir")
    else:
        with open(CVE_PATCH_PATH, "w") as write_file:
            json.dump(patch_url, write_file, sort_keys=True, indent=2)
        print("Founded {} patch url and dumped into json {}".format(length, CVE_PATCH_PATH))

def load_patch_json(patch):
    global patch_url
    if os.path.exists(patch):  
        patch_abs_path = os.path.abspath(patch) 
        with open(patch_abs_path, "r") as read_file:
            patch_url = json.load(read_file)
        print("Successfully loaded {}".format(patch))
    else:
        print("Error: {} not found".format(patch))

def search_cve(cveid):
    if cveid in patch_url.keys():
        print(cveid, patch_url[cveid])
    else:
        print("Error: not found {}".format(cveid))



def print_commit(json_file):
    global tmp_cveid
    global cve_commit
    global commit_find
    global rest_cve
    key_value=''
    if isinstance(json_file, dict):
        for key in json_file.keys():

            key_value = json_file.get(key)
            if key == "vulnerable_configuration" \
                or key == "vulnerable_configuration_cpe_2_2":
                continue
            if key == "id" or key == "ID" or key == "_id":
                # print(tmp_cveid)
                tmp_cveid = key_value
                
            if isinstance(key_value, dict):
                print_commit(key_value)
            elif isinstance(key_value, list):
                for json_array in key_value:  
                    print_commit(json_array)
            elif isinstance(key_value, str):
                print_commit(key_value)
    elif isinstance(json_file, list):
        for json_file_array in json_file:

            print_commit(json_file_array)
    elif isinstance(json_file, str):

        if json_file.find("commit") != -1 and \
            (json_file.startswith('http') or \
            json_file.startswith('https') or \
            json_file.startswith('ftp')):
            if json_file not in cve_commit[tmp_cveid]:
                commit_find += 1
                # print("[+]", tmp_cveid, "=", json_file)
                cve_commit[tmp_cveid].append(json_file)
        elif json_file.find("issues") != -1 and \
            (json_file.startswith('http') or \
            json_file.startswith('https') or \
            json_file.startswith('ftp')):
            if json_file not in cve_commit[tmp_cveid]:
                commit_find += 1
                # print("[+]", tmp_cveid, "=", json_file)
                cve_commit[tmp_cveid].append(json_file) 
            
        else:
            if tmp_cveid not in rest_cve:
                rest_cve.append(tmp_cveid)
            
    return commit_find    

def print_target_commit(target):
    f = open(target, encoding='utf-8')
    json_file = json.load(f)
    print(json_file)
    f.close()
    found = print_commit(json_file) 
    with open(CVE_TARGET_COMMIT_ISSUE, "w") as write_file:
        json.dump(cve_commit, write_file, sort_keys=True, indent=2)
    print("found {} commit url and dumped into {}".format(found, CVE_TARGET_COMMIT_ISSUE))

def circl_cve_search(cveid):
    global cve_commit
    global commit_find
    cve_commit.clear()
    cve_store_json = cveid+'.json'
    commit_store_json = cveid+'-commit.json'
    
    if not os.path.exists(cve_store_json):
        cmd = ['curl', 'http://cve.circl.lu/api/cve/{}'.format(cveid)]
        cve_json = str(subprocess.check_output(cmd, universal_newlines=True)).strip()
        with open(cve_store_json, "w") as write_file:
            write_file.write(cve_json)

    f = open(cve_store_json, encoding='utf-8')
    json_file = json.load(f)
    f.close()

    commit_find = 0
    found = print_commit(json_file) 
    if found != 0:
        with open(commit_store_json, "w") as write_file:
            json.dump(cve_commit, write_file, sort_keys=True, indent=2)
        print("[+] found {} commit url and dumped into {}".format(found, commit_store_json))  
    else:
        print("[-] sorry, we don't find any commit url there")
    pass

def cvelist_search_commit(cve_abs_dir):
    for root, dirs, files in os.walk(cve_abs_dir):
        for cve_json in files:
            # print(os.path.splitext(cve_json)[1])
            if os.path.splitext(cve_json)[1] == '.json':
                # print(os.path.join(root, cve_json))
                # cvelist/2005/4xxx/CVE-2005-4881.json
                # if cve_json == 'CVE-2005-4881.json':
                f = open(os.path.join(root, cve_json), encoding='utf-8')
                # print(cve_json)
                json_file = json.load(f)
                # print(json_file)
                f.close()
                found = print_commit(json_file)

    with open(CVEDIR_COMMIT_PATH, "w") as write_file:
        json.dump(cve_commit, write_file, sort_keys=True, indent=2)
    print("already dumped into {}".format(CVEDIR_COMMIT_PATH))   
    pass

def complete_task(target):
    global cve_commit
    f = open(target, encoding='utf-8')
    #res=f.read()
    json_file = json.load(f)

    f.close()
    found = print_commit(json_file)
    with open(CVE_TARGET_COMMIT_ISSUE, "w") as write_file:
        json.dump(cve_commit, write_file, sort_keys=True, indent=2)
    print("[+] found {} commit and issues url and dumped into {}".format(found, CVE_TARGET_COMMIT_ISSUE))
    circl_query = 0
    for d in json_file:
        for key in d.keys():
            if key == "_id" and (d[key] not in cve_commit.keys()):
                circl_query += 1
                print("[-]", d[key])
                # circl_cve_search(d[key])
            
    print("{} CVE commit/issue not found".format(circl_query))
    

def main(argc, argv):
    cfg = init_arg(argv)
    
    if hasattr(cfg, 'cve_abs_dir') and cfg.cve_abs_dir:
        if hasattr(cfg, 'cvedir_commit') and cfg.cvedir_commit:
            cvelist_search_commit(cfg.cve_abs_dir)
        else:
            load_cve_dir(cfg.cve_abs_dir)

    elif hasattr(cfg, 'patch') and cfg.patch:
        load_patch_json(cfg.patch)
    
    if hasattr(cfg, 'cveid') and cfg.cveid:
        if hasattr(cfg, 'circl') and cfg.circl:
            circl_cve_search(cfg.cveid)
        else:
            search_cve(cfg.cveid)

    if hasattr(cfg, 'target_json') and cfg.target_json:
               print_target_commit(cfg.target_json)

    if hasattr(cfg, 'task') and cfg.task:
        complete_task(cfg.task)
    return 0

if __name__ == '__main__':
    ret = main(len(sys.argv), sys.argv)
    sys.exit(ret)
