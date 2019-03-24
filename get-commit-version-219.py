import os
import sys
sys.path.append(os.path.abspath('../utils'))

#import magic
import db_operation
import udload
import hashlib
import shutil
import pymongo as pm
import os
import os.path
import subprocess
import json
"""
add the query unprocessed cve_commit_mata data
"""

def hashfile(f, blocksize=65536):
    """
    Compute hash value of the specified file
        ...here is sha256...
    Parameters:
        f, file path, type of string
    Return:
        hash value if success otherwise None
    """
    try:

        if not os.path.exists(f):
            return None

        afile = open(f, "rb")
        hasher = hashlib.sha256()
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)

        afile.close()
        return hasher.hexdigest()

    except Exception as e:
        print e
        afile.close()
        return None


def upload(fpath, commit, repo):
    try:
        hashvalue = hashfile(fpath)
        if hashvalue is None:
            return False
        hashvalue += '.zip'
        if udload.upload_to_ceph(fpath, hashvalue) == False:
            return False
        if db_operation.add_commit_version(hashvalue, commit, repo) < 0:
            return False
        return True
    except Exception, e:
        print e
        return False

def get_unprocessed_versions_by_SnapShot(cve_commits_meta,repo):
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    processed_commits= db_operation.query_commits_of_snapshots(repo)
    print 'processed:'+str(len(processed_commits))
    count =0
    for ccm in cve_commits_meta:
        _id = str(ccm['_id']['$oid'])
        #print _id
        for key in ccm.keys():
            if key == 'commit':
                commit = ccm[key]
                if commit in processed_commits:
                    print '[processed]', commit
                    count = count+1
                    continue
                db.unprocessed_cve_commit.insert({'commit':commit})

    print count


def obtain_versions_by_commits(cve_commits_meta, url_prefix, repo):
    processed_commits = db_operation.query_commits_of_snapshots(repo)

    for ccm in cve_commits_meta:
        _id = str(ccm['_id']['$oid'])
        print _id
        for key in ccm.keys():
            
            if key == 'commit': 
                commit = ccm[key]
                if commit in processed_commits:
                    print '[processed]', commit
                    continue
                cmd='wget -P ./'+_id+'/commit ' + url_prefix +str(commit)+'.zip'
                print('commit: '+cmd)
                #subprocess.call(cmd, shell=True)
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                our, err = process.communicate()
                errcode = process.returncode
                if errcode < 0:
                    print '[ERROE]', errcode, err
                    rm_path = './' + _id
                    if os.path.isdir(rm_path):
                        shutil.rmtree(rm_path)
                    continue
               
                # upload
                fpath = './' + _id + '/commit/' + str(commit) + '.zip'
                if not os.path.isfile(fpath):
                    print '[NO FILE EXISTED]'
                    continue
                upload(fpath, commit, repo)
                # clean
                if os.path.isdir('./' + _id):
                    shutil.rmtree('./' + _id)
                

            if key == 'parents_commits':
                parent_commit_list=ccm[key]
                for parent_commit in parent_commit_list:
                    if parent_commit in processed_commits:
                        print 'parents: processed:', parent_commit
                        continue
                    pcmd = 'wget -P ./' + _id + '/parent_commit ' + url_prefix + str(
                        parent_commit) + '.zip'
                    print('parent_commit: '+pcmd)
                    #subprocess.call(pcmd, shell=True)
                    process = subprocess.Popen(pcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    our, err = process.communicate()
                    errcode = process.returncode
                    if errcode < 0:
                        print '[ERROE]', errcode, err
                        rm_path = './' + _id
                        if os.path.isdir(rm_path):
                            shutil.rmtree(rm_path)
                        continue
               
                    # upload
                    fpath = './' + _id + '/parent_commit/' + str(parent_commit) + '.zip'
                    if not os.path.isfile(fpath):
                        print '[NO FILE EXISTED]'
                        continue
                    upload(fpath, parent_commit, repo)
                    # clean
                    if os.path.isdir('./' + _id):
                        shutil.rmtree('./' + _id)

        #break


if __name__ == '__main__':
   #client = pymongo.MongoClient('172.18.108.219', 27087)
   #db = client.imagemagick
   #cve_commits_meta = db.cve_commit_meta.find({})
   '''
   # for imagemagick
   url_pre='https://github.com/ImageMagick/ImageMagick/archive/' 
   repo = 35780977
   json_file = './imagemagick_commit_meta.json'
   json_file = './commit_meta_imagemagick.json'
   '''

   ''' 
   # for ffmpeg 
   url_pre='https://github.com/FFmpeg/FFmpeg/archive/'
   repo = 1614410
   json_file = './commit_meta_ffmpeg.json'

  
   # for openssl
   url_pre = 'https://github.com/openssl/openssl/archive/'
   repo = 7634677
   json_file = './commit_meta_openssl.json'
   '''
   #for php-src
   url_pre = 'https://github.com/php/php-src/archive/'
   repo = 1903522
   json_file = './commit_meta_php-src.json'

   cve_commits_meta = []
   with open(json_file, 'r') as f:
       for line in f.readlines():
           cmm = json.loads(line)
           cve_commits_meta.append(cmm)
   #print cve_commits_meta
   #obtain_versions_by_commits(cve_commits_meta, url_pre, repo)
   get_unprocessed_versions_by_SnapShot(cve_commits_meta, repo)
