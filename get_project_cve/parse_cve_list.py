import csv
import pymongo as pm
import re
def read_csv(file,db):
    csv_rows = []
    with open(file,'r',encoding='utf-8',errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)
        title = reader.fieldnames
        print(title)
        for row in reader:
            csv_rows.extend([{title[i]:row[title[i]] for i in range(len(title))}])
            #db.item.insert_one({title[i]:row[title[i]] for i in range(len(title))})
        return csv_rows
def parse_cves(db):
    db.item_str.remove({})
    items =  db.item.find({})
    for item in items:
        cve={}
        cve['id']=item['Name']
        cve['status']=item['Status']
        cve['desc']=item['Description']
        refs = list(item['References'].split('|'))
        cve['refs']=[]
        for i in range(len(refs)):
            ref ={}
            #print(refs[i])
            if re.match('.*?URL:.*?',refs[i],re.S)!=None:
                ref['url'] = re.sub('\s','',refs[i])
                result = re.search('URL:(.*)',refs[i],re.I)
                print(result[0],result[1])
                ref['url']=result[1]
                ref['info']=re.sub('\s','',refs[i-1])
                cve['refs'].append(ref)

            elif re.match('.*?(http.*)|(ftp.*)',refs[i],re.I)!=None:
                ref['url'] = re.sub('\s', '', refs[i])
                result = re.search('.*?(http.*)|(ftp.*)', refs[i], re.I)
                print(result[0],result[1],result[2])
                if result[1]!=None:
                    ref['url'] = result[1]
                elif result[2]!=None:
                    ref['url']=result[2]
                cve['refs'].append(ref)
        cve['votes']=[]
        votes = item['Votes'] .split('|')
        for vote in votes:
            if vote =='':
                continue
            else:
                cve['votes'].append(vote)
        cve['comments']=[]
        comments = item['Comments'].split('|')
        for comment in comments:
            if comment =='':
                continue
            else:
                cve['comments'].append(comment)

        db.item_str.insert_one(cve)

if __name__ =='__main__':
    client = pm.MongoClient('172.18.108.169', 21000)
    db = client.cve
    #db.item.remove({})
    #db.item.insert_many(read_csv('allitems.csv',db))
    parse_cves(db)
