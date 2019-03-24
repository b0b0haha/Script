import pymongo as pm
import re
def is_related_commit(db,cve,commit):
    result = db.cve_commit.find({'cve':cve,'commit':commit})
    if result.count()>0:
        return False
    else:
        return True

if __name__ == "__main__":
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.php_src
    #result = db.cve.find({'refs.url':{'$regex':'https://github.com/FFmpeg/FFmpeg/commit/[0-9a-z]+'}})
    result = db.cve.find({})
    #print result[0]
    count = 0
    for cve in result:
        cm = db.cve_commit.find({'cve':cve['_id']})
        #print cve['_id'], cm.count()
        if cm.count() == 0:
            print cve['_id']
            for ref in cve['refs']:
                if 'url' in  ref.keys():
                    url = ref['url']
                    #print url
                    # m = re.match(re.escape('https://github.com/FFmpeg/FFmpeg/commit/') + '[0-9a-z]{40}', url)
                    # m1 = re.match(re.escape('http://git.ffmpeg.org/?p=ffmpeg;a=commit;h=')+'[0-9a-z]{40}', url)
                    # if m is not None or m1 is not None:
                    #    print url
                    if 'https://github.com/php/php-src/commit/' in url:
                        print '\t\t', url
                        sha = url.split('/')[-1].strip()
                        print sha, cve['desc']
                        cve_commit = {}
                        if is_related_commit(db,cve['_id'],sha):
                            cve_commit['cve'] = cve['_id']
                            cve_commit['commit'] = [sha]
                            cve_commit['patch_version'] = None
                            #db.cve_commit.insert_one(cve_commit)
                            count = count+1
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
                                #db.cve_commit.insert_one(cve_commit)
                                count = count+1
    print count

