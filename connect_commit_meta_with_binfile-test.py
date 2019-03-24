import os
import sys
reload(sys)
sys.setdefaultencoding('UTF8')
sys.path.append(os.path.abspath('../utils'))

import db_operation
import pymongo

def query_src2bin(function_name, filename, commit):
    try:
        conn = db_operation.connect_to_db_simple()
        sql = "select A.debug_file, B.tag, B.filename from S_ImageMagick_Src2Bin as A, S_ImageMagick_Bin as B where A.function_name like '%s' and \
               A.debug_file = B.id and B.tag like '%s' and A.source_file like '%%%s';"%(function_name, commit, filename)
        #print sql
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        if len(result) > 0:
            return result
        
        return []
    except Exception as e:
        print e
        return []

def query():
    try:
        client = pymongo.MongoClient('172.18.108.219', 27087)
        db = client.imagemagick
        commit_metas = db.cve_commit_meta.find({})
        count_existed = 0
        count_notexisted = 0
        count = 0
        print commit_metas.count()
        #exit(0)
        for cm in commit_metas:
            print 'count:', count
            count += 1
            commit = cm['commit']
            parent_commits = []
            if 'parents_commits' in cm.keys(): 
                parent_commits = cm['parents_commits'] 
            else:
                print "cm.keys:", cm.keys()
                #break
            if cm['files'] is None:
                continue
            for f in cm['files']:
                filename = f['filename'] 
                if f['headings'] is None:
                    continue
                for heading in f['headings']:
                    func_name = heading.split('(')[0]
                    func_name = func_name.split(' ')[-1]
                    func_name = func_name.strip('*')
                    print 'func_name:', func_name, 'filename:', filename, 'commit:', commit         
                    src2bin = query_src2bin(func_name, filename, commit)
                    print src2bin
                    if src2bin == []:
                        count_notexisted += 1
                    else:
                        count_existed += 1
                    print 'have:', count_existed, 'not have:', count_notexisted, '\n'
                    #exit(0)
    except Exception as e:
        print e
        return False

if __name__ == "__main__":
    query()
    print 'end'
