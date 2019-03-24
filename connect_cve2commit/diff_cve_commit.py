import pymongo as pm
def diff_cve_commit():
    client = pm.MongoClient("172.18.108.219",27087)
    db = client.php_src
    cve_commit_lbc = list(db.cve_commit_lbc.find({}))
    cve_commit  = list(db.cve_commit.find({}))
    print len(cve_commit_lbc)
    count = 0
    for item in cve_commit_lbc:
        if db.cve_commit.find({'commit':item['commit']},{'cve':item['cve']}):
            count = count+1
    print count

def aggregate_cve_commit(db):
    result = db.cve_commit.aggregate([{'$group':{'_id':'$cve','commit':{'$push':'$commit'}}}])
    for item in result:
        db.cve_commit_test.insert(item)
        db.cve_commit_unique.insert({'commit':item['commit'],'cve':item['_id']})


if __name__ == "__main__":
    #diff_cve_commit()
    aggregate_cve_commit()

