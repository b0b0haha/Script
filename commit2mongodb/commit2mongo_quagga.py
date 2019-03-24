#coding:utf-8
'''
缺少的部分：
1、文件上传下载的解析功能，chunkdata,heading 字段缺少
2、缺少commit对应的版本信息
'''
import os
import sys
import timeit

sys.path.append(os.path.abspath('../utils'))

import db_operation_A
import udload
import pymongo as pm
import io
import bson
import re

import MySQLdb
import time
import random
import re

DB_IP='172.18.100.15'
DB_NAME='_github_crawler'
DB_VM_NAME='db_sf_338'
DB_USER='github_crawler'
DB_PASS ='github_crawler'


def connect_to_db(db_ip, db_user, db_pass, db_name):
    try:
        start = timeit.default_timer()
        db = MySQLdb.connect(db_ip, db_user, db_pass, db_name)
        db.set_character_set('utf8')
        end = timeit.default_timer()
        print('connect time: ' + str(end - start))
        if (db == None):
            return None

        return db
    except Exception as e:
        print e
        return None

def connect_to_db_simple():
    db = None
    count = 5
    while True:
        count = count - 1
        db = connect_to_db(DB_IP,DB_USER,DB_PASS,DB_NAME)
        if db is not None or count < 0:
            break

        random.seed()
        time.sleep(random.randint(1, 5))
    return db

'''
def download_filecontent(uri):
    path = uri
    if not udload.download_from_commonstorage(uri, path):
        print 'download failed'
        return None
    content = None
    with io.open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    #content = [bson.code.Code(x) for x in content.split('\n')]
 
    os.remove(path)

    return content

def parse_function_headings(filename, content):
    if not filename.lower().endswith('.c') and not filename.lower().endswith('.h'):
        return None
    headings = []
    prog = re.compile('[0-9]+')
    for l in content.split('\n'):
        if l.startswith('@@'):
            elems = l.split('@@')
            #print elems[1]
            if elems[-1] == '':
                continue
            chunk = {}
            m = prog.findall(elems[1])
            chunk['from_lineno'] = int(m[0])
            chunk['from_lines'] = int(m[1])
            chunk['to_lineno'] = int(m[2])
            chunk['to_lines'] = int(m[3])
            chunk['heading'] = elems[-1]
            #print chunk
            headings.append(chunk)
                
    if len(headings) == 0:
        return None

    return headings
'''

def process_commitfiles(files):
    try:
        commit_files = []
        for sha, filename, previous_name, status, additions, deletions, changes, patch_local_url in files:
            result = {}
            result['sha'] = sha
            result['filename'] = filename
            result['previous_name'] = previous_name
            result['status'] = status
            result['additions'] = int(additions)
            result['deletions'] = int(deletions)
            result['changes'] = int(changes)
            '''
            
            #读取commit的文件内容
            content = download_filecontent(patch_local_url)
            print(content)

            if content is not None:
                headings = parse_function_headings(filename, content)
                #print headings
                content = bson.code.Code(content)
                result['chunks_meta'] = headings
            result['content'] = content
            '''
            result['chunks_meta']=None
            result['content']=None

            commit_files.append(result)

        return commit_files
    except Exception, e:
        print e
        return None

if __name__ == "__main__":
    client = pm.MongoClient('172.18.108.169', 21000)
    db= client.quagga
    quagga = 3470062
    conn = connect_to_db_simple()
    #get the commit info related to the project
    start = timeit.default_timer()
    commits = db_operation_A.query_repo_commits(quagga,conn)
    end = timeit.default_timer()
    print ('query_repo_commits time: '+str(end-start))
    print(len(commits))
    count = 0
    for sha, author_id, committer_id, stats_additions, stats_deletions, stats_total in commits:
        start = timeit.default_timer()
        count +=1
        if count == 500:
            conn.close()
            conn = connect_to_db_simple()
            count = 0
        print sha, author_id, committer_id, stats_additions, stats_deletions, stats_total

        if db.commit.find({'_id':sha}).count()!=0:
            continue

        commit = {}
        commit['_id'] = sha
        commit['stats'] = {'additions':stats_additions, 'deletions':stats_deletions, 'total':stats_total}
        if author_id is not None:
            start = timeit.default_timer()
            author = db_operation_A.query_nameduser(author_id,conn)
            commit['author'] = author
            end = timeit.default_timer()
            print('query_nameduser time: ' + str(end - start))
            #print author
        if committer_id is not None:
            start = timeit.default_timer()
            committer =  db_operation_A.query_nameduser(committer_id,conn)
            #print committer
            commit['committer'] = committer
            end = timeit.default_timer()
            print('query_nameduser time: ' + str(end - start))
        # 获取commit对应的版本号
        #versions = db_operation.query_commit_tag(quagga, sha)

        commit['versions'] = None
        files = db_operation_A.query_commit_files(sha,conn)
        files = process_commitfiles(files)
        commit['files'] = files
        #print files

        parents = db_operation_A.query_commit_parents(sha,conn)
        commit['parents'] = parents
        #print parents

        gitcommit = db_operation_A.query_gitcommit(sha,conn)
        if gitcommit is not None and gitcommit['message'] is not None:
            gitcommit['message_t'] = gitcommit['message']
            gitcommit['message'] = bson.code.Code(gitcommit['message'])
            #print gitcommit
            commit['gitcommit'] = gitcommit
        print commit
        db.commit.insert_one(commit)
        end = timeit.default_timer()
        print ('all time: ' + str(end - start))
        #break


