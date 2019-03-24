#coding: utf-8


import requests
from urllib.parse import urlencode
from urllib.parse import quote
from pyquery.pyquery import PyQuery as pq
import xlrd
import xlwt
from xlutils.copy import copy

import os
import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

import pymongo
from termcolor import colored
import subprocess
import re
import linecache
import time
import datetime
import bson

client = pymongo.MongoClient('172.18.108.169', 21087)
db = client.pdns
base_url = 'https://github.com/PowerDNS/pdns/commit/'
#base_url = 'https://github.com/isc-projects/bind9/commit/'
headers = {
    'host': 'github.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
}

def _print_exception(e = None):
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    if e is not None:
        print(e)
    print(colored('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj), 'red'))

def parse_function_headings_v2(filename, content):
    #if not filename.lower().endswith('.c') and not filename.lower().endswith('.h'):
    #    return None
    try:
        if filename.split('.')[-1].lower() not in ['c', 'cc', 'cpp', 'h', 'hpp', 'hh']:
            return None
        headings = []
        prog = re.compile('[0-9]+')
        chunk_line_count = 0
        heading = None
        from_lineno = None
        from_lines = None
        to_lineno = None
        to_lines = None
        is_block_tail = False
        is_block_head = False
        is_block_change = False
        for l in content.split('\n'):
            #print colored(l, 'red')
            #print colored('hhhh' + str(heading), 'red')
            if len(l) > 0 and l[-1] == '\r':
                l = l[:-1]
            if l.startswith('@@'):

                if is_block_change and heading is not None:
                    chunk = {}
                    chunk['from_lineno'] = from_lineno
                    chunk['from_lines'] = from_lines
                    chunk['to_lineno'] = to_lineno
                    chunk['to_lines'] = to_lines
                    chunk['heading'] = heading
                    ##print chunk
                    headings.append(chunk)

                heading = None
                chunk_line_count = 0
                is_block_tail = False
                is_block_change = False

                elems = l.split('@@')
                #print elems[1]
                if elems[1] != '':
                    m = prog.findall(elems[1])
                    #print m
                    from_lineno = int(m[0])
                    from_lines = int(m[1])
                    to_lineno = int(m[2])
                    to_lines = int(m[3])
                    heading = elems[-1]
                    #print (colored('heading: ' + heading, 'yellow'))

            else:

                if len(l) > 1 and l[1] == '}':
                    is_block_tail = True

                    if is_block_change and heading is not None:
                        chunk = {}
                        chunk['from_lineno'] = from_lineno
                        chunk['from_lines'] = from_lines
                        chunk['to_lineno'] = to_lineno
                        chunk['to_lines'] = to_lines
                        chunk['heading'] = heading
                        ##print chunk
                        headings.append(chunk)

                    heading = None
                    is_block_head = False
                    is_block_change = False
                    continue

                if len(l) > 1 and ((ord(l[1]) >= 65 and ord(l[1]) <= 90) or (ord(l[1]) >= 97 and ord(l[1]) <= 122) or ord(l[1]) == 95): #and (':' not in l):
                    heading = l[1:]
                    #print(colored('AAAA'+ heading, 'green'))
                    is_block_change = False
                    #continue

                if len(l.strip()) > 1 and (l[0] == '-' or l[0] == '+'):
                    #print(colored(l, 'green'))
                    is_block_change = True

        #print 'is_block_change', is_block_change, 'heading', heading
        if is_block_change and heading is not None:
            chunk = {}
            chunk['from_lineno'] = from_lineno
            chunk['from_lines'] = from_lines
            chunk['to_lineno'] = to_lineno
            chunk['to_lines'] = to_lines
            chunk['heading'] = heading
            #print 'BBBB', chunk
            headings.append(chunk)

        #print 'headings:', headings
        if len(headings) == 0:
            return None

        return headings
    except Exception as e:
        _print_exception(e)
        return None

def list_git_log(code_path):
    try:
        if not os.path.isdir(code_path):
            print(colored('Not a directory: ' + str(code_path), 'red'))
            return None
        cwd = os.getcwd()
        commit_log = os.path.join(cwd, '.temp/commit.log')
        
        cmd = 'cd ' + code_path + ' && '
        cmd += 'git log > ' + commit_log + ' && '
        cmd += 'cd ' + cwd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err is not None and err.strip() != '':
            print(colored(err, 'red'))
            return None
        commits_sha1 = []
        with open(commit_log, 'r') as f:
            for line in f:
                if not line.startswith('commit'):
                    continue
                sha1 = line.split(' ')[1][:-1]
                commits_sha1.append(sha1)
                #break
        print(colored('Total size: ' + str(len(commits_sha1)), 'green'))
        os.remove(commit_log)
        return commits_sha1
    except Exception as e:
        _print_exception(e)
        return None

def show_git_commit(sha1, code_path):
    try:
        if not os.path.isdir(code_path):
            print(colored('Not a directory: ' + str(code_path), 'red'))
            return None
        cwd = os.getcwd()
        cmd = 'cd ' + code_path + ' && '
        cmd += 'git show --pretty=raw ' + sha1 + ' && '
        cmd += 'cd ' + cwd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err.strip() != '':
            print(colored(err, 'red'))
            return None
        #print out
        lines = out.split('\n')
        #print 'AAA', lines
        commit = {}
        commit['parent'] = []
        commit['message'] = ''
        head_flag = True
        content_flag = False
        files = []
        file_tmp = {}
        content_tmp = ''
        for l in lines:
            if head_flag and l.startswith('commit '):
                commit['_id'] = l.split(' ')[1]
            if head_flag and l.startswith('tree'):
                commit['tree'] = l.split(' ')[1]
            if head_flag and l.startswith('parent '):
                commit['parent'].append(l.split(' ')[1])
            if head_flag and l.startswith('author '):
                author_tmp = {}
                author_tmp['name'] = l[7:l.find('<')].strip()
                author_tmp['email'] = l[l.find('<')+1:l.find('>')]
                author_tmp['date'] = datetime.datetime.fromtimestamp(float(l.split(' ')[-2]))
                author_tmp['tail'] = l.split(' ')[-1]
                commit['author'] = author_tmp
            if head_flag and l.startswith('committer '):
                committer_tmp = {}
                committer_tmp['name'] = l[10:l.find('<')].strip()
                committer_tmp['email'] = l[l.find('<')+1:l.find('>')]
                committer_tmp['date'] = datetime.datetime.fromtimestamp(float(l.split(' ')[-2]))
                committer_tmp['tail'] = l.split(' ')[-1]
                commit['committer'] = committer_tmp
            if head_flag and l.strip() == '':
                continue
            if head_flag and l.startswith('    '):
                commit['message'] += l.strip() + '\n'
            if l.startswith('diff --git '):
                head_flag = False
                content_flag = False
                if content_tmp != '':
                    content_tmp = content_tmp[:-1]
                    headings = parse_function_headings_v2(file_tmp['filename'], content_tmp)
                    file_tmp['chunks_meta'] = headings
                    #file_tmp['content'] = bson.code.Code(content_tmp)
                if file_tmp != {}:
                    files.append(file_tmp)
                file_tmp = {}
                content_tmp = ''
            if l.startswith('--- '):
                #print l
                file_tmp['previous'] = l.split(' ')[1][2:]
            if l.startswith('+++ '):
                file_tmp['filename'] = l.split(' ')[1][2:]
                content_flag = True
                continue
            if content_flag:
                content_tmp += l + '\n'
             
        if content_tmp != '':
            #print 'BBB', file_tmp
            #print 'CCC', content_tmp
            headings = parse_function_headings_v2(file_tmp['filename'], content_tmp)
            file_tmp['chunks_meta'] = headings
            #file_tmp['content'] = bson.code.Code(content_tmp)
        if file_tmp != {}:
            files.append(file_tmp)
        if len(files) > 0:
            commit['files'] = files
        if 'message' in commit:
            commit['message'] = commit['message'][:-1]
        
        #print colored(str(commit), 'green')
        
        return commit
    except Exception as e:
        _print_exception(e)
        return None 

def _insert_one(coll, doc):
    try:
        coll.insert_one(doc)
    except Exception as e:
        _print_exception(e)
def list_git_tag(code_path):
    try:
        if not os.path.isdir(code_path):
            print(colored('Not a directory: '+str(code_path)),'red')
            return None
        cwd = os.getcwd()
        tag_log = os.path.join(cwd,'.temp/tag.log')
        cmd = 'cd '+code_path +'&&'
        cmd +='git tag > '+tag_log +'&&'
        cmd+='cd '+cwd
        print(cmd)
        p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err = p.communicate()
        if err is not None and err.strip()!='':
            print(colored(err,'red'))
            return None
        tags=[]
        with open(tag_log,'r') as f:
            for line in f:
                tag = line.strip()
                tags.append(str(tag))
                #break
        print(colored('Total size: '+str(len(tags)),'green'))
        os.remove(tag_log)
        return tags

    except Exception as e:
        _print_exception(e)
        return None

def show_git_tag(tag,code_path):
    try:
        if not os.path.isdir(code_path):
            print(colored('Not a directory: '+str(code_path)),'red')
            return None
        cwd = os.getcwd()
        cmd = 'cd '+code_path +'&&'
        cmd +='git show '+tag +'&&'
        cmd+='cd '+cwd
        print(cmd)
        p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err = p.communicate()
        if err is not None and err.strip()!='':
            print(colored(err,'red'))
            return None
        lines = out.split('\n')
        for line in lines:
            if not line.startswith('commit'):
                continue
            else:
                commit = line.split(' ')[1]
                break
        print(commit)
        return (commit)


    except Exception as e:
        _print_exception(e)
        return None

def get_miss_file(commit):
    url = base_url+commit
    print(url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.text

            with open('sha_content.html','w+',encoding='UTF-8') as f:
                f.writelines(content)

            doc =pq(content)
            items= doc('.js-diff-progressive-container')
            files=[]
            infos= items.find('.file-header.file-header--expandable.js-file-header ')
            num = len(infos)
            print(num)
            for i in range(0,num):
                file={}
                id = '#diff-'+str(i)
                div = items.find(id)
                with open('sha.html', 'w+', encoding='UTF-8') as f:
                    f.writelines(str(div))
                file_infos = div.find('.file-header.file-header--expandable.js-file-header')
                file['filename']=file_infos.attr('data-path')
                print(file['filename'])
                if file['filename'].split('.')[-1].lower() not in ['c', 'cc', 'cpp', 'h', 'hpp', 'hh']:
                    continue
                if file_infos.attr('data-file-deleted')=='false':
                    file['previous'] = file_infos.attr('data-path')
                else:
                    file['previous'] =''
                print(file)
                chunks_meta=[]
                chunk_infos= div.find('.blob-code.blob-code-inner.blob-code-hunk').text().split('@@')
                chunk_infos.remove('')
                print(chunk_infos)
                i=0
                while i<len(chunk_infos):
                    lines = chunk_infos[i].split(' ')
                    print(lines)
                    chunk_meta={}
                    to_lines =lines[2].split('+')[-1]
                    to_lines=to_lines.split(',')
                    print(to_lines)
                    if len(to_lines)==2:
                        chunk_meta['to_lines'] = to_lines[1]
                        chunk_meta['to_lineno'] = to_lines[0]
                    else:
                        chunk_meta['to_lineno'] = to_lines[0]
                        chunk_meta['to_lines']=''
                    from_lines=lines[1].split('-')[-1]
                    from_lines = from_lines.split(',')
                    if len(from_lines)==2:
                        chunk_meta['from_lines'] = from_lines[1]
                        chunk_meta['from_lineno'] = from_lines[0]
                    else:
                        chunk_meta['from_lineno'] = from_lines[0]
                        chunk_meta['from_lines']=''

                    chunk_meta['heading']=chunk_infos[i+1]
                    chunks_meta.append(chunk_meta)
                    i=i+2
                print(len(chunks_meta))
                file['chunks_meta']=chunks_meta
                files.append(file)
        return files

    except requests.ConnectionError as e:
        print('error:', e.args)
        return None

def add_file2gitcommit():
    git_commits = db.git_commit.find({},no_cursor_timeout=True)
    gcount=0
    for git_commit in git_commits:
        if 'files' not in git_commit or git_commit['files']==None:
            git_commit['files'] = get_miss_file(git_commit['_id'])
            db.git_commit.update({'_id': git_commit['_id']}, git_commit)
            gcount+=1
            print(colored(gcount,'green'))
    git_commits.close()

def list_version_commit(code_path):
    #获取每个版本的commit并存入mongodb中
    git_tags = db.git_tag.find({},no_cursor_timeout=True)
    vdb = client.iscbind_commits
    count=0
    for git_tag in git_tags:
        tag = git_tag['tag']
        commit = git_tag['commit']
        print(tag,commit)
        cwd = os.getcwd()
        cmd = 'cd ' + code_path + ' && '
        cmd += 'git reset --hard ' + commit + ' && '
        commit_log = os.path.join(cwd, '.temp/'+tag+'_commit.log')
        cmd += 'git log > ' + commit_log + ' && '
        cmd += 'cd ' + cwd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err is not None and err.strip() != '':
            print(colored(err, 'red'))
            return None
        commits= []
        with open(commit_log, 'r') as f:
            for line in f:
                if not line.startswith('commit'):
                    continue
                sha1 = line.split(' ')[1][:-1]
                commits.append(sha1)
                # break
        print(colored('Total size: ' + str(len(commits)), 'green'))
        os.remove(commit_log)
        vdb[tag + '_commits'].remove({})
        for commit in commits:
            vdb[tag + '_commits'].insert_one({'commit':commit})
        count+=1
    git_tags.close()
def get_commit_version(sha,code_path):
    git_commit = db.git_commit.find_one({'_id':sha})
    git_tags = list(db.git_tag.find({}).sort('date', 1))
    count =0
    if git_commit!=None:
        date = git_commit['author']['date']
        print(date)
        i=0
        while i<len(git_tags):
            if (date <= git_tags[i]['date']):
                tag=git_tags[i]['tag']
                commit =git_tags[i]['commit']
                cwd = os.getcwd()
                cmd = 'cd ' + code_path + ' && '
                cmd += 'git reset --hard ' + commit + ' && '
                commit_log = os.path.join(cwd, '.temp/' + tag + '_commit.log')
                cmd += 'git log > ' + commit_log + ' && '
                cmd += 'cd ' + cwd
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                if err is not None and err.strip() != '':
                    print(colored(err, 'red'))
                    return None
                commits = []
                with open(commit_log, 'r') as f:
                    for line in f:
                        if not line.startswith('commit'):
                            continue
                        sha1 = line.split(' ')[1][:-1]
                        commits.append(sha1)
                        # break
                #print(colored('Total size: ' + str(len(commits)), 'green'))
                os.remove(commit_log)
                if sha in commits:
                    print('ok',tag,sha)
                    return tag
                    break
                else:
                    i+=1
                    print('false')
            else:
                i+=1

def get_security_commit_version(code_path):
    '''
    获取与安全相关的commit的版本
    :return:
    '''
    security_commits =db.security_commit.find({},no_cursor_timeout=True)
    for commit in security_commits:
        if db.git_commit.find_one({'_id':commit['id']})!=None:
            commit['master']='true'
            commit['versions']=get_commit_version(commit['id'],code_path)
            affect_version = []
            if commit['parents'] != None:
                for parent in commit['parents']:
                    version = get_commit_version(parent,code_path)
                    if version != None:
                        affect_version.append(version)
            commit['affect_version'] = affect_version
        else:
            commit['master']='false'
        db.security_commit.update({'_id':commit['_id'],'id': commit['id']},commit)
    security_commits.close()

def get_need_info():
    #获取文件有多处修改的commit
    '''

    commits = db.git_commit.find({})
    for commit in commits:
        if 'files' in commit:
            files = commit['files']
            for file in files:
                if file['chunks_meta'] != None:
                    if len(file['chunks_meta']) != 1:
                        print(commit['_id'])
                        break
    '''
    #获取文件为空的commit

    git_commits =db.git_commit.find({})
    count=0
    commits =[]
    for git_commit in git_commits:
        if 'files' not in git_commit or git_commit['files'] == None:
            print(colored('commit: '+git_commit['_id']+','+'count: '+str(count),'green'))
            commits.append(git_commit)
            count+=1
    with open('nofile_commit.txt','w+',encoding='UTF-8') as f:
        for commit in commits:
            f.write(str(commit)+'\n')
    print(count)


    #获取所有没有master字段的commit
    '''
    commits = db.security_commit.find({},no_cursor_timeout=True)
    count=0
    pcount=0
    db.confirm_security_commit.remove({})
    for commit in commits:
        if 'master' not in commit.keys():
            count+=1

        else:
            if commit['master']=='true':
                pcount+=1
                db.confirm_security_commit.insert_one(commit)
    print(count,pcount)
    commits.close()
    '''
    #获取没有files字段的security_commit
    '''
    commits = db.security_commit.find({})
    count=0
    for commit in commits:
        if 'files' not in commit.keys():
            count+=1
        else:
            print('ok')
    print(count)
    '''


def add_file2commit():
    #往确认的与安全相关的commit中添加文件信息
    commits = db.confirm_security_commit.find({})
    for commit in commits:
        git_commit = db.git_commit.find_one({'_id':commit['id']})
        if git_commit!=None:
            if 'files' in git_commit.keys():
                files = git_commit['files']
                commit['git_files'] = files
            else:
                commit['git_files'] = None
        else:
            commit['git_files']=get_miss_file(commit['id'])
        db.confirm_security_commit.update({'_id':commit['_id'],'id':commit['id']},commit)

def get_security_versions_list():
    #获取与安全相关的commit的版本统计
    commits = db.confirm_security_commit.find({})
    db.security_version.remove({})
    for commit in commits:
        affect_versions = commit['affect_version']
        if affect_versions!=None and len(affect_versions)!=0:
            for affect_version in affect_versions:
                version = db.security_version.find_one({'version': affect_version})
                if version !=None:
                    version['count']+=1
                    version['commits'].append(commit['id'])
                    db.security_version.update({'version':affect_version},version)
                else:
                    security_version = {}
                    security_version['version'] = affect_version
                    security_version['count'] = 1
                    security_commits =[]
                    security_commits.append(commit['id'])
                    security_version['commits'] =security_commits
                    db.security_version.insert_one(security_version)
    with open('security_version.txt','w+') as f:
        versions =db.security_version.find({}).sort('count',-1)
        for version in versions:
            f.write(version['version']+': '+str(version['count'])+'\n')

def add_file_xls(path):
    #将commit的文件信息添加到表格中
    workbook= xlrd.open_workbook(path)
    table = workbook.sheets()[1]
    newb = copy(workbook)
    wbsheet = newb.get_sheet(1)
    commits = table.col_values(9)
    count=0
    pcount=0
    records =[]
    for commit in commits:
        if count==0:
            count += 1
            continue
        commit= commit.strip()
        if commit!='':
            pcount+=1
            print(commit)
            record={}
            git_commit = db.git_commit.find_one({'_id':commit})
            if git_commit!=None:
                files = ''
                for file in git_commit['files']:
                    if (file['filename'].split('.')[-1].lower() not in ['c', 'cc', 'cpp', 'h', 'hpp', 'hh']):
                        continue
                    cfile = ''
                    cfile += file['filename']
                    print(cfile)
                    headings = []
                    if file['chunks_meta'] != None:
                        cfile += ':'
                        for chunk in file['chunks_meta']:
                            if chunk != None:
                                heading = str(chunk['heading']) + '@@' + str(chunk['to_lines']) + ',' + str(
                                    chunk['to_lineno']) + ' ' + str(chunk['from_lines']) + ',' + str(
                                    chunk['from_lineno']) + '@@'
                                headings.append(heading)
                    cfile += '|'.join(headings)
                    print(cfile)
                    files += cfile
                record['commit']=commit
                record['files'] = files
                wbsheet.write(count,10,files)
                print(files)
                records.append(record)
            else:
                files = ''
                gfiles = get_miss_file(commit)
                for file in gfiles:
                    if (file['filename'].split('.')[-1].lower() not in ['c', 'cc', 'cpp', 'h', 'hpp', 'hh']):
                        continue
                    cfile = ''
                    cfile += file['filename']
                    print(cfile)
                    headings = []
                    if file['chunks_meta'] != None:
                        cfile += ':'
                        for chunk in file['chunks_meta']:
                            if chunk != None:
                                heading = str(chunk['heading']) + '@@' + str(chunk['to_lines']) + ',' + str(
                                    chunk['to_lineno']) + ' ' + str(chunk['from_lines']) + ',' + str(
                                    chunk['from_lineno']) + '@@'
                                headings.append(heading)
                    cfile += '|'.join(headings)
                    print(cfile)
                    files += cfile
                record['commit'] = commit
                record['files'] = files
                wbsheet.write(count, 10, files)
                print(files)
                records.append(record)
        wbsheet.write(count, 12, base_url + commit)



        count += 1
    print(pcount)
    print(len(records))
    newb.save(path)
    with open('record.txt','w+') as f:
        for record in records:
            f.write(record['commit'] + ',' + record['files'] + '\n\n')

def get_git_commit_version():
    git_commits = db.git_commit.find({},no_cursor_timeout=True)
    for commit in git_commits:
        sha = commit['_id']
        commit['version']= get_commit_version(sha,'./pdns')
        db.git_commit.update({'_id':sha},commit)

if __name__ == "__main__":
    '''
    sha = 'd5b61afd9ef8bdea6ced4598e74caafab6c612c1'
    files = get_miss_file(sha)
    with open('files.txt','w+') as f:
        f.write(str(files))
    '''
    #get_need_info()
    add_file_xls('pdns-cve.xlsx')

    '''

    db.git_commit.remove({})
    commits_sha1 = list_git_log('./bind9')
    count = 1
    for sha1 in commits_sha1:
        print(colored(sha1+'\tcount:'+str(count), 'blue'))
        #if sha1 != '3ed852eea50f9d4cd633efb8c2b054b8e33c2530':
        #    continue
        if db.git_commit.find({'_id':sha1}).count() > 0:
            print (colored('[DUPLICATE]', 'red'))
            continue
        commit = show_git_commit(sha1, './bind9')
        _insert_one(db.git_commit, commit)
        #break
        #if count > 5:
        #    break
        count += 1
    '''
    # add_file2gitcommit()
    #get_git_commit_version()

    '''
    
    tags = list_git_tag('./bind9')
    db.git_tag.remove({})
    for tag in tags:
        git_tag={}
        commit = show_git_tag(tag, './bind9')
        sha = db.git_commit.find_one({'_id':commit})
        if sha!=None:
            #print(sha.keys())
            if 'files' in sha and sha['files']!=None:
                git_tag['files'] = sha['files']
            else:
                git_tag['files']=''
            git_tag['date']=sha['author']['date']
            git_tag['parent']=sha['parent']
            git_tag['message']=sha['message']
            git_tag['tree']=sha['tree']
            git_tag['master']='true'
        else:
            sha = show_git_commit(commit,'./bind9')
            print(sha.keys())
            if 'files' in sha and sha['files']!=None:
                git_tag['files'] = sha['files']
            else:
                git_tag['files'] = ''
            git_tag['date'] = sha['author']['date']
            git_tag['parent'] = sha['parent']
            git_tag['message'] = sha['message']
            git_tag['tree'] = sha['tree']
            git_tag['master'] = 'false'
        if db.git_tag.find_one({'tag': tag}) != None:
            continue
        git_tag['tag']=tag
        git_tag['commit']=commit
        db.git_tag.insert_one(git_tag)
        #break
    '''
    # list_version_commit('./bind9')
    # version =get_commit_version('5c889cf5921bac43bec8461b89dd463fb45b0d83','./pdns')
    # print(version)
    # get_security_commit_version('./bind9')
    # add_file2commit()
    # get_security_versions_list()












