#coding:utf-8
#import sys
#reload(sys)
#print sys.getdefaultencoding()

#sys.setdefaultencoding('UTF8')

import pymongo
import os
import re
import requests
from urllib.parse import urlencode
from urllib.parse import quote
from pyquery.pyquery import PyQuery as pq
#client = pymongo.MongoClient('172.18.108.219', 27087)
#db = client.ffmpeg
base_url = 'https://www.cvedetails.com'
headers = {
    'host': 'www.cvedetails.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
}
def aggregate_cve_commit(db):
    '''
    聚合cve_commit
    :param db:
    :return:
    '''
    db.cve_commit_unique.remove({})
    result = db.cve_commit.aggregate([{'$group':{'_id':'$cve','commit':{'$push':'$commit'}}}])
    for item in result:
        comm={}
        comm['commit']=item['commit']
        comm['cve']=item['_id']
        result = db.cve_details.find_one({'CVE_ID':item['_id']})
        if result!=None and 'Vulnerability Type' in result and 'vuln_prods_table'in result:
            comm['vuln_type'] = result['Vulnerability Type']
            comm['version'] = result['vuln_prods_table']
            db.cve_commit_unique.insert(comm)
        else:
            comm['vuln_type']=''
            comm['version']=''
            db.cve_commit_unique.insert(comm)



def constuct_cve_commit_unique_content(db):
    all_cve_commits = db.cve_commit_unique.find({})
    count = 0
    for cm in all_cve_commits:
        if cm['commit'] is None:
            continue
        haved = False
        for c in cm['commit']:
            ct = db.commit.find_one({'_id':c})
            if ct is None:
                continue
            if len(ct['files']) == 0:
                continue
            cve_commit_meta = {}
            cve_commit_meta['cve'] = cm['cve']
            files = []
            for f in ct['files']:
                print (cm['cve'], f['filename'])
                '''
                这里的haved在可读取文件后要注掉
                '''
                haved = True
                if 'chunks_meta' in f.keys():
                    if f['chunks_meta'] is None:
                        continue
                    haved = True
                    headings = []
                    for chunk in f['chunks_meta']:
                        if chunk['heading'] not in headings:
                            headings.append(chunk['heading'])
                        # print '\t', chunk['heading']
                    print ('\t', headings)
                    files.append({'filename': f['filename'], 'headings': headings})
            if haved:
                count += 1
                cve_commit_meta['files'] = files
                cve_commit_meta['commit'] = c
                cve_commit_meta['parent_commits'] = db.commit.find_one({'_id':c})['parents']
                cve_commit_meta['vuln_type'] = cm['vuln_type']
                cve_commit_meta['version'] = cm['version']
                conn = db.cve_commit.find_one({'cve':cm['cve'],'commit':c})
                cve_commit_meta['patch_version'] = conn['patch_version']
                print (cve_commit_meta)
                db.cve_commit_meta.insert_one(cve_commit_meta) 

    print (count)

def append_clusterfuzz_testcase(db):
    security_commits = db.security_commit.find()
    count = 0
    haved = []
    pattern = r'[f/F]ixes: [0-9]+/'
    for sc in security_commits:
        if 'cherry picked' in sc['gitcommit']['message_t']:
            continue
        print (sc)
        '''
        new_append = False
        continuing = True
        have_matched = False
        for line in sc['gitcommit']['message_t'].split('\n'):
            #print line
            m = re.match(pattern, line)
            if m is not None:
                have_matched = True
                #print line[:-1]
                if line[:-1] in haved:
                    print line[:-1], sc['_id']
                    continuing = False
                    continue
                new_append = True
                haved.append(line[:-1])

        if not have_matched or not new_append:
            #print sc['gitcommit']['message_t']
            continue
        '''
  
        if len(sc['files']) == 0:
            print ('=0', sc)
        cve_commit_new = {}
        #if 'clusterfuzz-testcase-minimized' in sc['gitcommit']['message_t']:
        #    pass
        #    #print sc['gitcommit']['message_t']
        #else:
        #    print sc['gitcommit']['message_t']
        #    count += 1
        
        cve_commit_new['cve'] = None
        files = []
        if len(sc['files'])>0:
            for f in sc['files']:
                if 'chunks_meta' in f.keys():
                    if f['chunks_meta'] is None:
                        # print 'chunks meta none'
                        files.append({'filename': f['filename'], 'headings': None})
                        # print files
                        continue
                    headings = []
                    for chunk in f['chunks_meta']:
                        if chunk['heading'] not in headings:
                            headings.append(chunk['heading'])
                    files.append({'filename': f['filename'], 'headings': headings})
        cve_commit_new['files'] = files
        cve_commit_new['commit'] = sc['_id']

        cve_commit_new['parent_commits'] = sc['parents']
        count += 1
        if db.cve_commit_meta.find({'commit':{'$regex':sc['_id']}}).count() == 0:
            db.cve_commit_meta.insert_one(cve_commit_new)
        count += 1
        if db.cve_commit_meta.find({'commit':{'$regex':sc['_id']}}).count() == 0:
            #db.cve_commit_meta.insert_one(cve_commit_new)
            #print cve_commit_new
            pass
        #break
    print (count)

def append_cve_not_in_related(db):
    all_cves = db.cve.find({})
    count = 0
    for cve in all_cves:
        result = db.cve_commit_unique.find({'cve':cve['_id']})
        if result.count() == 0:
            print(cve['_id'])
            cve_commit_new = {}
            cve_commit_new['cve'] = cve['_id']
            cve_commit_new['commit'] = None
            cve_commit_new['patch_version'] = None
            db.cve_commit_unique.insert_one(cve_commit_new)
            count += 1
    print(count)

def add_info_by_person():
    cve={}
    cve['CVE_ID']='CVE-2017-3135'
    cve = get_cve_details(cve)
    print(cve)
    return(cve)

if __name__ == "__main__":
    client = pymongo.MongoClient('172.18.108.169', 21087)
    db = client.iscbind
    db.cve_commit_meta.delete_many({})
    aggregate_cve_commit(db)
    constuct_cve_commit_unique_content(db)
    cves = db.cve_commit_meta.find({})




