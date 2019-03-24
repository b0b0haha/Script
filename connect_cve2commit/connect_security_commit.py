#coding:utf-8
import pymongo as pm
import re
import os
import sys
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except(TypeError,ValueError):
        pass
    return False
def get_related_cve():
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    cves = db.cve_commit.find({})
    id =[]
    for cve in cves:
        if cve['cve'] not in id:
            id.append(cve['cve'])
            db.cve_test.insert(db.cve.find({'_id':cve['cve']}))
    print len(id)
def get_not_related_cve():
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    cve_related = db.cve_related.find({})
    cves = db.cve.find({})
    id =[]
    for cve_re in cve_related:
        id.append(cve_re['_id'])
    for item in cves:
        if item['_id'] in id:
            continue
        db.cve_norelated.insert_one(item)
    print db.cve_norelated.find({}).count()
def is_related_commit(db,cve,commit):
    result = db.cve_commit.find({'cve':cve,'commit':commit})
    if result.count()>0:
        return False
    else:
        return True
def connect_cve2commit_github():
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    # result = db.cve.find({'refs.url':{'$regex':'https://github.com/FFmpeg/FFmpeg/commit/[0-9a-z]+'}})
    result = db.cve.find({})
    # print result[0]
    count = 0
    for cve in result:
        cm = db.cve_commit.find({'cve': cve['_id']})
        # print cve['_id'], cm.count()
        if cm.count() == 0:
            print cve['_id']
            for ref in cve['refs']:
                if 'url' in ref.keys():
                    url = ref['url']
                    # print url
                    # m = re.match(re.escape('https://github.com/FFmpeg/FFmpeg/commit/') + '[0-9a-z]{40}', url)
                    # m1 = re.match(re.escape('http://git.ffmpeg.org/?p=ffmpeg;a=commit;h=')+'[0-9a-z]{40}', url)
                    # if m is not None or m1 is not None:
                    #    print url
                    if 'https://github.com/php/php-src/commit/' in url:
                        print '\t\t', url
                        sha = url.split('/')[-1].strip()
                        print sha, cve['desc']
                        cve_commit = {}
                        if is_related_commit(db, cve['_id'], sha):
                            cve_commit['cve'] = cve['_id']
                            cve_commit['commit'] = [sha]
                            cve_commit['patch_version'] = None
                            # db.cve_commit.insert_one(cve_commit)
                            count = count + 1
                    if 'git.php.net' in url:
                        print '\t\t', url
                        sha = url.split('h=')[1].strip()
                        print len(sha)
                        if len(sha) == 40:
                            print sha, cve['desc']
                            cve_commit = {}
                            if is_related_commit(db, cve['_id'], sha):
                                cve_commit['cve'] = cve['_id']
                                cve_commit['commit'] = [sha]
                                cve_commit['patch_version'] = None
                                # db.cve_commit.insert_one(cve_commit)
                                count = count + 1
    print count

def connect_cve2commit_cve():

    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    cve_commit = db.commit.find({"gitcommit.message_t":{'$regex':'cve','$options':'i'}})
    print cve_commit.count()
    nore_cve = db.cve_norelated.find({})
    nocve_id =[]
    count = 0
    for item in nore_cve:
        nocve_id.append(item['_id'])
    print len(nocve_id)
    for item in cve_commit:
        #gitcommit.message_t

        gitcommit = item['gitcommit']
        message_t = gitcommit['message_t']
        index = re.search('cve-',message_t,re.I)
        if index:
            tag = index.span()
            cve_id = str(message_t[tag[0]:tag[0]+13]).upper()
            #print cve_id,type(cve_id)
            if cve_id in nocve_id:
                count = count+1
                cve_commit = {}
                cve_commit['cve'] =cve_id
                cve_commit['commit'] = item['_id']
                cve_commit['patch_version'] = None
                cve = db.cve_norelated.find({'_id': cve_id})
                cve_t = db.cve_related.find({'_id': cve_id})
                print cve.count(),cve_t.count()
                if cve.count() == 1 and cve_t.count() == 0:
                    print cve[0]
                    db.cve_related.insert_one(cve[0])
                    db.cve_norelated.remove(cve[0])
    print count

def connect_cve2commit_fixbug():
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    cve_count =0
    commit_count =0
    cve_result = db.cve.find({"refs.url": {'$regex': 'https://bugs.php.net/bug.php?'}})
    bugIDs=[]
    for cve in cve_result:
        refs = cve['refs']
        for ref in refs:
            bugId=''
            url = ref['url']
            index = url.find('https://bugs.php.net/bug.php?id=')
            if index>=0:
                id = url.split("=")[1:]
                for char in id:
                    bugId+=char
                #print bugId
                bugIDs.append(bugId)

                
                commit_result = db.commit.find({'gitcommit.message_t': {'$regex': bugId, '$options': 'i'}})
                commit_count =commit_count+ commit_result.count()
                for commit in commit_result:
                    cve_commit = {}
                    cve_commit['cve'] = cve['_id']
                    cve_commit['commit'] = commit['_id']
                    cve_commit['patch_version'] = None
                    db.cve_commit.insert_one(cve_commit)


    print commit_count
    print len(bugIDs)

def connect_by_person():
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    result = db.cve.find({'_id':'CVE-2017-6441'})
    print result.count()
    for item in result:
        cve_commit = {}
        cve_commit['cve'] = item['_id']
        cve_commit['commit'] = 'd46169468359e85084fcacba41b8ed94f2edfbe2'
        cve_commit['patch_version'] = None
        db.cve_commit.insert_one(cve_commit)
        db.cve_related.insert_one(item)
        db.cve_norelated.remove(item)


if __name__ =="__main__":
    """
    
    #connect_cve2commit_fixbug()
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    #get_related_cve()
    #get_not_related_cve()
    #connect_by_person()
    re_cve = db.cve_related.find({}).count()
    nre_cve = db.cve_norelated.find({}).count()
    cve = db.cve.find({}).count()
    if re_cve+nre_cve==cve:
        print True
    """
    #connect_cve2commit_cve()
    #get_related_cve()
    get_not_related_cve()


