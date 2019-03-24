import os
import sys
sys.path.append(os.path.abspath('../utils'))

import db_operation
import udload
import pymongo as pm
import io
import bson
import re


def download_filecontent(uri):
    path = uri
    if not udload.download_from_commonstorage(uri, path):
        print 'download failed'
        return None

    content = None
    with io.open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    #content = [bson.code.Code(x) for x in content.split('\n')]
 
    #os.remove(path)
    print('ok')
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

            content = download_filecontent(patch_local_url)
            if content is not None:
                headings = parse_function_headings(filename, content)
                #print headings
                content = bson.code.Code(content)
                result['chunks_meta'] = headings
            result['content'] = content
            commit_files.append(result)

        return commit_files
    except Exception, e:
        print e
        return None

if __name__ == "__main__":
    content = download_filecontent('4d4bd1e9185dc08424c03c3ea013aa0215d92cf4c71839aa21ee06386228b3a2.patch')
    print(content)

    '''
    client = pm.MongoClient('172.18.108.219', 21087)
    db= client.iscbind

    iscbind = 112236924
    #get the commit info related to the project
    commits = db_operation.query_repo_commits(iscbind)
    for sha, author_id, committer_id, stats_additions, stats_deletions, stats_total in commits:
        print sha, author_id, committer_id, stats_additions, stats_deletions, stats_total
        commit = {}
        commit['_id'] = sha
        commit['stats'] = {'additions':stats_additions, 'deletions':stats_deletions, 'total':stats_total}
        if author_id is not None:
            author = db_operation.query_nameduser(author_id)
            commit['author'] = author
            #print author
        if committer_id is not None:
            committer =  db_operation.query_nameduser(committer_id)
            #print committer
            commit['committer'] = committer

        versions = db_operation.query_commit_tag(pdns, sha)
        commit['versions'] = versions
        files = db_operation.query_commit_files(sha)
        files = process_commitfiles(files)
        commit['files'] = files
        #print files

        parents = db_operation.query_commit_parents(sha)
        commit['parents'] = parents
        #print parents

        gitcommit = db_operation.query_gitcommit(sha)
        if gitcommit is not None and gitcommit['message'] is not None:
            gitcommit['message_t'] = gitcommit['message']
            gitcommit['message'] = bson.code.Code(gitcommit['message'])
            #print gitcommit
            commit['gitcommit'] = gitcommit
        print commit
        
        db.commit.insert_one(commit)
        #break
        '''
