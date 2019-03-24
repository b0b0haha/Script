import os
import sys
import json
import pymongo
'''
PROJECT_NAME='quagga'
HOST = '172.18.108.169'
PORT =21000
KEYWORD =['quagga']
client = pymongo.MongoClient(HOST,PORT)
db = client[PROJECT_NAME]
'''
PROJECT_NAME='pdns'
HOST = '172.18.108.169'
PORT =21087
KEYWORD =['powerdns','pdns','power dns']
client = pymongo.MongoClient(HOST,PORT)
db = client[PROJECT_NAME]


'''

PROJECT_NAME='iscbind'
HOST = '172.18.108.169'
PORT =21000
KEYWORD =['isc bind','isc ']
client = pymongo.MongoClient(HOST,PORT)
db = client[PROJECT_NAME]
'''
def get_unconfirmed_cve(keyword):
    '''
    cve中利用正则表达式筛出来的cve
    :return:
    '''
    db.unconfirmed_cve.delete_many({})

    for key in keyword:
        match = 0
        cve = list(client.cve.item_str.find({'desc':{'$regex':key,"$options":'i'}}))
        print('get:',len(cve))
        for item in cve:
            cve_meta = {}
            if db.cve.find({'id':item['id']}).count()==1:
                match+=1
            else:
                if db.unconfirmed_cve.find({'id':item['id']}).count()==0:
                    db.unconfirmed_cve.insert_one(item)
                    if db.cve_meta.find({'_id':item['id']}).count()==0:
                        cve_meta['_id']=item['id']
                        refs=[]
                        for ref in item['refs']:
                            refs.append(ref)
                        cve_meta['refs']=refs
                        db.cve_meta.insert_one(cve_meta)

        unmatch = len(cve)-match
        print(key,'match:',match,'unmatch',unmatch)




def get_cve_meta():
    '''
    cve_details筛出来的cve
    :return:
    '''
    db.cve_meta.delete_many({})
    db.cve.delete_many({})
    cve = client.cve.item_str
    cve_details = db.cve_details.find({})
    cve_meta ={}
    for item in cve_details:
        cve_meta['_id'] = item['CVE_ID']
        cve_url= []
        cve_result = list(cve.find({'id':item['CVE_ID']}))
        if len(cve_result)==1:
            if db.cve.find({'id':cve_meta['_id']}).count()==0:
                db.cve.insert_one(cve_result[0])
            cve_refs =cve_result[0]['refs']
            print(cve_refs)
            for i in range(len(cve_refs)):
                cve_url.append(cve_refs[i])
            cve_details_refs = item['vuln_refs_table']
            for url in cve_details_refs:
                flag = True
                for ref in cve_url:
                    print(ref)
                    if url == ref['url']:
                        flag = False
                        break
                if flag == True:
                    cve_url.append({'url':url})
                else:
                    continue
            cve_meta['refs']=cve_url
        if db.cve_meta.find({"_id":cve_meta['_id']}).count()== 0:
            db.cve_meta.insert_one(cve_meta)

if __name__=='__main__':

    get_cve_meta()
    get_unconfirmed_cve(KEYWORD)
























