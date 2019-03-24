import pymongo as pm
import os

if __name__ == "__main__":
    client = pm.MongoClient('172.18.108.219', 27087)
    db = client.ffmpeg

    cve_commits = db.cve_commit.find({})
    print cve_commits[0]
    print 'cve', cve_commits[0]['cve']
    print 'commits', cve_commits[0]['commit']

    for cm in cve_commits:
        if cm['commit'] is not None:
            print cm['cve']
            print cm['commit']
            for m in cm['commit']:
                db.commit.update_one(
                   {'_id': m},
                   {'$set':{'cve':cm['cve']}}
                )
            #break
        #print cm
