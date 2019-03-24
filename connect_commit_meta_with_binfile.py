#coding:utf-8
import os
import sys
reload(sys)
sys.setdefaultencoding('UTF8')
sys.path.append(os.path.abspath('../utils'))

import db_operation
import pymongo
import udload
import subprocess
import json
import datetime
import hashlib

def hashfile(filepath, blocksize=65536):
    with open(str(filepath),"rb") as file:
        sha1obj = hashlib.sha1()
        sha1obj.update(file.read())
        hash = sha1obj.hexdigest()
        print(hash)
        return hash
def upload(dot_path, svg_path, function_address, tag, par_tag):

    try:
        #get the file's hashcode
        dot_hashvalue = hashfile(dot_path)
        svg_hashvalue = hashfile(svg_path)

        if dot_hashvalue is None or svg_hashvalue is None :
            return False
        if udload.upload_to_ceph(dot_path, dot_hashvalue) == False or udload.upload_to_ceph(svg_path, svg_hashvalue) == False :
            return False
        if db_operation.add_ImageMagick_match(dot_hashvalue, svg_hashvalue, function_address, tag, par_tag) < 0:
            return False
        return True
    except Exception, e:
        print e
        return False

def query_src2bin(function_name, filename, commit):
    try:
        conn = db_operation.connect_to_db_simple()
        sql = "select B.local_url,A.function_address from S_ImageMagick_Src2Bin as A, S_ImageMagick_Bin as B where A.function_name like '%s' and \
               A.debug_file = B.id and B.tag like '%s' and A.source_file like '%%%s' and A.source_file not like '%%./.libs/%%';"%(function_name, commit, filename)
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

def query(json_file):
    try:
        #client = pymongo.MongoClient('172.18.108.219', 27087)
        #db = client.imagemagick
        commit_metas = []
        with open(json_file, 'r') as f:
            for line in f.readlines():
                cmm = json.loads(line)
                commit_metas.append(cmm)
        #commit_metas = db.cve_commit_meta.find({})
        count_existed = 0
        count_notexisted = 0
        count = 0
        count =  len(commit_metas)
        #exit(0)
        for cm in commit_metas:
            fcount =0
            print 'count:', count
            #count += 1
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
                fcount = fcount +1
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
                    pcount = 0
                    if src2bin == []:
                        count_notexisted += 1
                    else:
                        file_url = src2bin[0][0]
                        cur_address = src2bin[0][1]
                        count_existed += 1
                        count = count + 1
                        cur_file = "/home/varas/tools/ImageMagick_compile/func_file/" + 'cur_commit-' + str(
                            commit) + "-file_" + str(
                            fcount) + "-" + str(
                            func_name) + "-" + str(cur_address)

                        if not udload.download_from_commonstorage(file_url,
                                                                  '/home/varas/tools/ImageMagick_compile/func_file/cur_commit-' + str(
                                                                      commit) + "-file_" + str(
                                                                      fcount) + "-" + str(
                                                                      func_name) + "-" + str(cur_address)):
                            print 'download failed'
                            continue
                        print 'success'
                        curfile_hash = str(hashfile(cur_file))
                        curfile_hash_path = "/home/varas/tools/ImageMagick_compile/func_file/" + curfile_hash + ".o"
                        if os.path.exists(cur_file) and curfile_hash is not None:
                            os.rename(cur_file, curfile_hash_path)


                    if pcount == len(parent_commits):
                        continue
                    for parent_commit in  parent_commits :
                        # print parent_commit
                        par_src2bin = query_src2bin(func_name, filename, parent_commit)
                        if par_src2bin == []:
                            continue
                        parent_url = par_src2bin[0][0]
                        par_address = par_src2bin[0][1]
                        if parent_url == None:
                            continue
                        if len(parent_url) == 0:
                            # print "fail to access the binary file"
                            continue

                        # 下载对应的二进制文件
                        pcount = pcount + 1
                        parent_commitId = parent_commit
                        par_file = "/home/varas/tools/ImageMagick_compile/func_file/" + 'parent_commit' + '-' + str(
                            parent_commit) + "-file_" + str(fcount) + "-" + str(func_name) + "-" + str(
                            par_address)

                        if not udload.download_from_commonstorage(parent_url,
                                                                  '/home/varas/tools/ImageMagick_compile/func_file/parent_commit' + '-' + str(
                                                                          parent_commit) + "-file_" + str(
                                                                      fcount) + "-" + str(func_name) + "-" + str(
                                                                      par_address)):
                            print 'download failed'
                            continue
                        print 'success'
                        parfile_hash = str(hashfile(par_file))
                        parfile_hash_path = "/home/varas/tools/ImageMagick_compile/func_file/" + str(
                            hashfile(par_file)) + ".o"
                        if os.path.exists(par_file) and parfile_hash is not None:
                            os.rename(par_file, parfile_hash_path)
                        # 进行文件内容存储
                        if cur_address != '0' and par_address != "0":
                            flag = db_operation.add_ImageMagick_FileInfo(str(commit), str(parent_commit),
                                                                         curfile_hash + ".o", parfile_hash + ".o",
                                                                         filename, cur_address,
                                                                         par_address)

                    print 'have:', count_existed, 'not have:', count_notexisted, '\n'
                    #exit(0)

    except Exception as e:
        print e
        return False

if __name__ == "__main__":
    query("/home/varas/tools/ImageMagick_compile/ImageMagick_commit_meta_json.json")
    print 'end'
