import pymongo
import re
import requests
import os
from pyquery.pyquery import PyQuery as pq

PROJECT_NAME='quagga'
HOST = '172.18.108.169'
PORT =21000
KEYWORD =['quagga ']
client = pymongo.MongoClient(HOST,PORT)
db = client[PROJECT_NAME]

def get_related_source():
    '''
    获取ref表
    :return:
    '''
    db.refs.delete_many({})
    pattern = re.compile('[a-zA-Z]+://(.*?)/(.*?)')
    items = db.cve_meta.find({})
    for item in items:
        for ref in item['refs']:
            refs = {}
            result = re.match(pattern,str(ref['url']))
            print(ref)
            if result !=None:
                ref['url']=re.sub('\s','',ref['url'])
                refs['ref'] = ref['url']
                refs['host'] = str(result.group(1))
                text = ref['url'].split("/")[-1]
                if text != '':
                    refs['text'] = text
                else:
                    text = ref['url'].split("/")[-2]
                    refs['text'] = text
                refs['cve'] = item['_id']
                print(refs)
                db.refs.insert_one(refs)
def get_hot_refs(index):
    '''
    获取链接的引用次数，并可返回指定排位的链接
    在每次更新ref表后都需要运行一次
    :param index:
    :return:
    '''
    items= list(db.refs.find({}))
    refs ={}
    for item in items:
        if item['host'] in refs:
            refs[item['host']]+=1
        else:
            refs[item['host']] = 1
    sorted_refs = sorted(refs.items(), key=lambda refs: refs[1], reverse=True)

    '''
    获取指定host的所有的链接
    '''
    db.ref_str.delete_many({})
    for i in range(len(sorted_refs)):
        count = 0
        host = sorted_refs[i][0]
        refs = db.refs.find({'host':host})
        url =[]
        for ref in refs:
            ref['ref']=re.sub('\s','',ref['ref'])
            if ref['ref'] not in url:
                count+=1
                url.append(ref['ref'])
        ref_str={}
        ref_str['host']=host
        ref_str['url']=url
        ref_str['count']=count
        db.ref_str.insert_one(ref_str)
    result = list(db.ref_str.find().sort('count',pymongo.DESCENDING))
    print(result[0])
    file_path = os.path.join(os.getcwd(), 'quagga-refs.txt')
    if os.path.exists(file_path):
        os.remove(file_path)
    for item in result:
        with open(file_path, 'a+') as f:
            f.write(str(item['host'])+' '+str(item['count']) + '\n')
    db.ref_str.delete_many({})
    for i in range(len(result)):
        print(result[i]['host'],result[i]['count'])
        db.ref_str.insert_one(result[i])
    ref_strs = list(db.ref_str.find({}))
    print (ref_strs[index])

    return ref_strs[index]['host']


def get_url_count():
    '''
    获取总的链接个数
    :return:
    '''
    cve_meta =db.cve_meta.find({})
    cve_count =0
    refs_count=db.refs.find({}).count()
    for cve in cve_meta:
        for ref in cve['refs']:
            cve_count+=1
    print('cve_url:',cve_count,'refs_url:',refs_count)


def get_connected_commit():
    '''
    获取已经关联的commit
    :return:
    '''
    commit_id=[]
    connect_commit = db.cve_commit.find({})
    for item in connect_commit:
        commit_id.append(item['commit'])
    return commit_id


def connect_cve2commit_cve():
    '''
    直接利用cve编号进行关联
    :return:
    '''
    #db.cve_commit.remove({})
    cve_commit = db.commit.find({"gitcommit.message_t":{'$regex':'[\s]*cve','$options':'i'}})
    print (cve_commit.count())
    for item in cve_commit:
        gitcommit = item['gitcommit']
        message_t = gitcommit['message_t']
        index = re.search('cve-',message_t,re.I)
        if index:
            tag = index.span()
            cve_id = str(message_t[tag[0]:tag[0]+13]).upper()
            if db.cve_commit.find({'cve':cve_id,'commit':item['_id']}).count()==0:
                cve_commit = {}
                cve_commit['cve'] = cve_id
                cve_commit['commit'] = item['_id']
                cve_commit['patch_version'] = None
                db.cve_commit.insert_one(cve_commit)

def connect_cve2commit_bugzilla():
    '''
    利用bugzilla编号进行关联
    :return:
    '''
    refs = db.ref_str.find({'host':{'$regex':'bugzilla','$options':'i'}})
    for ref in refs:
        host = ref['host']
        print(host)
        commit_result = db.commit.find({'gitcommit.message_t': {
            '$regex': '(bugzilla)[\s]*#[\d]+|(bz)[\s]*#[\d]+|bz[\s]+|bugzilla', '$options': 'i'}})
        text = 'show_bug.cgi?id='
        count = 0
        print(commit_result.count())
        for commit in commit_result:
            gitmessage = commit['gitcommit']['message_t']
            print(gitmessage)
            results = re.findall('#([\d]+)', gitmessage, re.I)
            for result in results:
                id = str(result)
                print('id: '+id)
                refs = db.refs.find({'host': host})
                for ref in refs:
                    url = ref['ref']
                    re_result = re.search('id=([\d]+).*', url, re.S)
                    #print(re_result.group(1))
                    if re_result != None and re_result.group(1) == id:
                        print(re_result.group(1), url)
                        if db.cve_commit.find({'cve': ref['cve'], 'commit': commit['_id']}).count() == 0:
                            cve_commit = {}
                            cve_commit['cve'] = ref['cve']
                            cve_commit['commit'] = commit['_id']
                            cve_commit['patch_version'] = None
                            db.cve_commit.insert_one(cve_commit)
                            count += 1

    print(count)


def get_securityfocus_url():
    '''
    利用securityfocus_url搜寻更多的链接
    :return:
    '''
    results = db.refs.find({'host':'www.securityfocus.com'})
    print('securityfocus:',results.count())
    for result in results:
        url = result['ref']+'/references'
        headers = {
            'host': result['host'],
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        }
        print(url)
        try:
            response = requests.get(url)
            if response.status_code ==200:
                context = response.text
                doc=pq(context)
                items = doc('#vulnerability a').items()
                for item in items:
                    ref= item.attr('href')
                    # 更新cve_meta，并且往refs插数据
                    if db.refs.find({'ref':ref,'cve':result['cve']}).count()==0:
                        cve_meta =db.cve_meta.find_one({'_id':result['cve']})
                        cve_meta['refs'].append({'url':ref})
                        print (cve_meta)
                        modified_count =db.cve_meta.update_one({'_id':result['cve']},{'$set':cve_meta})
                        print(modified_count)
                        items = db.cve_meta.find({})
                        pattern = re.compile('[a-zA-Z]+://(.*?)/(.*?)')
                        match = re.match(pattern, str(ref))
                        refs={}
                        if match != None:
                            ref = re.sub('\s','',ref)
                            refs['ref'] = ref
                            refs['host'] = str(match.group(1))
                            text = ref.split("/")[-1]
                            if text != '':
                                refs['text'] = text
                            else:
                                text = ref.split("/")[-2]
                                refs['text'] = text
                            refs['cve'] = result['cve']
                            print(refs)
                            db.refs.insert_one(refs)


        except requests.ConnectionError as e:
            print('error',e.args)

def connect_cve2commit_github(rule):
    refs = list(db.refs.find({'ref':{'$regex':'github','$options':'i'}}))
    pattern = re.compile(rule)
    if len(refs)>0:
        for ref in refs:
            result = re.match(pattern,ref['ref'])
            if result !=None:
                sha = re.sub('\s','',ref['text'])
                print(sha)
                if db.commit.find({'_id':sha}).count()>0:
                    if db.cve_commit.find({'cve': ref['cve'], 'commit': sha}).count() == 0:
                        cve_commit = {}
                        cve_commit['cve'] = ref['cve']
                        cve_commit['commit'] = sha
                        cve_commit['patch_version'] = None
                        db.cve_commit.insert_one(cve_commit)

def connect_cve2commit_quagga_dev():
    '''
       通过quagga.net站点进行匹配
       :return:
       '''
    # 通过‘quagga-dev’进行匹配
    refs = db.refs.find({'ref':{'$regex':'quagga-dev','$options':'i'}})
    for ref in refs:
        result = re.match('([\d]+)\.html$', ref['text'], re.S)
        if result !=None:
            print(result.group(1))
            id_str = str(result.group(1))
            id =''
            index =0
            for i in range(len(id_str)):
                if id_str[i]!='0':
                    index=i
                    break
            for k in range(index,len(id_str)):
                id+=id_str[k]
            print(id)
            commits = db.commit.find({'gitcommit.message_t': {'$regex': 'quagga-dev '+id, '$options': 'i'}})
            print(commits.count())


def connect_cve2commit_quagga():

    #直接通过gogs.quagga.net中的文件信息进行匹配
    refs = db.refs.find({'ref': {'$regex': 'gogs.quagga.net', '$options': 'i'}})
    for ref in refs:
        text = ref['text']
        commits = db.commit.find({'gitcommit.message_t': {'$regex':text, '$options': 'i'}})
        if commits.count()>0:
            for commit in commits:
                if db.cve_commit.find({'cve': ref['cve'], 'commit':commit['_id']}).count() == 0:
                    cve_commit = {}
                    cve_commit['cve'] = ref['cve']
                    cve_commit['commit'] = commit['_id']
                    cve_commit['patch_version'] = None
                    db.cve_commit.insert_one(cve_commit)


def get_secuity_commit(type,pattern):
    re_rule ={}
    db.security_commit.remove({'type':type})
    connected_commit = get_connected_commit()
    commit_result = db.commit.find({'gitcommit.message_t': {'$regex': pattern, '$options': 'i'}})
    pattern_str = re.compile(pattern, re.I)

    count =0
    for commit in commit_result:
        result = re.search(pattern_str,commit['gitcommit']['message_t'])
        if result!=None:
            print(result)
            if commit['_id'] not in connected_commit:
                count += 1
                commit_t={}
                commit_t['id']=commit['_id']
                commit_t['files']=commit['files']
                commit_t['stats']=commit['stats']
                commit_t['versions']=commit['versions']
                commit_t['parents']=commit['parents']
                commit_t['gitcommit']=commit['gitcommit']
                commit_t['type'] = type
                if db.security_commit.find({'type':type,'_id':commit['_id']}).count()==0:
                    db.security_commit.insert_one(commit_t)
    if db.re_rule.find({'type':type}).count()>0:
        re_rule = db.re_rule.find_one({'type':type})
        re_rule['pattern']=pattern
        re_rule['count']=count
        db.re_rule.update_one({'type':type},{'$set':re_rule})
    else:
        re_rule['type']=type
        re_rule['pattern']=pattern
        re_rule['count'] = count
        db.re_rule.insert_one(re_rule)
    print(commit_result.count())
    print(count)


def get_security_commit_db():
    db.security_commit.remove({})
    re_rules =db.re_rule.find({})
    for re_rule in re_rules:
        type=re_rule['type']
        pattern = re_rule['pattern']
        print(type,pattern)
        get_secuity_commit(type,pattern)

def connect_by_person(cve,commit):
    cve_commit = {}
    cve_commit['cve'] = cve
    cve_commit['commit'] = commit
    cve_commit['patch_version'] = None
    if db.cve_commit.find({'cve':cve,'commit':commit}).count()==0:
        db.cve_commit.insert_one(cve_commit)

def get_info(info):
    commit_result = db.commit.find({'gitcommit.message_t': {'$regex':info, '$options': 'i'}})
    print('commit: '+str(commit_result.count()))
    for commit in commit_result:
        print(commit['_id'])

def connect_cve2commit_url_byID():
    res= db.ref_str.find({'host':'support.avaya.com'})
    urls = res[0]['url']
    for url in urls:
        #直接匹配末尾的内容
        result = url.split('/')[-1]
        commit_result = db.commit.find(
            {'gitcommit.message_t': {'$regex': result, '$options': 'i'}})
        for commit in commit_result:
            refs = db.refs.find({'ref': url})
            cve_comm = {}
            for ref in refs:
                cve_comm['cve'] = ref['cve']
                cve_comm['commit'] = commit['_id']
                cve_comm['patch_version'] = None
                if db.cve_commit.find({'cve': ref['cve'], 'commit': commit['_id']}).count() == 0:
                    print(cve_comm)
                    db.cve_commit.insert_one(cve_comm)

        '''
        #匹配链接末尾ID
        result = re.search('[\d]+', str(url.split('/')[-1]))
        if result != None:
            id = result[0]
            print(id)
            commit_result = db.commit.find(
                {'gitcommit.message_t': {'$regex': '#' + str(id) + '[\s]*', '$options': 'i'}})
            if commit_result.count() != 0:
                for commit in commit_result:
                    message_t = commit['gitcommit']['message_t']
                    result = re.search('#([\d]+).*', message_t)
                    if result != None:
                        print('result:' + str(result[0]) + ' ' + str(result[1]))
                        if result[1] == id:
                            refs = db.refs.find({'ref': url})
                            cve_comm = {}
                            for ref in refs:
                                cve_comm['cve'] = ref['cve']
                                cve_comm['commit'] = commit['_id']
                                cve_comm['patch_version'] = None
                                if db.cve_commit.find({'cve': ref['cve'], 'commit': commit['_id']}).count() == 0:
                                    print(cve_comm)
                                    db.cve_commit.insert_one(cve_comm)
        '''
        '''
        #直接匹配commitID
        result = re.search('h=(.*)', str(url.split('/')[-1]))
        id = result[1]
        print(id)
        cve_comm = {}
        refs = db.refs.find({'ref': url})
        for ref in refs:
            cve_comm['cve'] = ref['cve']
            cve_comm['commit'] = id
            cve_comm['patch_version'] = None
            if db.cve_commit.find({'cve': ref['cve'], 'commit': id}).count() == 0:
                print(cve_comm)
                db.cve_commit.insert_one(cve_comm)
         '''




if __name__=='__main__':

    #

    #get_hot_refs(3)
    #get_url_count()
    #get_securityfocus_url()
    #get_hot_refs(0)
    #connect_cve2commit_url()
    #get_url_count()

    #get_info()
    '''
    get_related_source()
    get_hot_refs(0)
    get_url_count()
    get_securityfocus_url()
    get_hot_refs(0)
    get_url_count()
    '''
    '''
    db.cve_commit.remove({})
    connect_cve2commit_cve()
    connect_cve2commit_bugzilla('bugzilla.quagga.net')
    connect_cve2commit_github('.*?://github.com/Quagga/quagga/commit/.*')
    connect_cve2commit_quagga()
    #quagga-dev没有匹配到东西
    connect_cve2commit_quagga_dev()
    '''
    ''' 
    type='bug'
    pattern_str ='bug'
    get_secuity_commit(type,pattern_str)
    '''
    #get_security_commit_db()

    '''
    #get_hot_refs(0)
    connect_cve2commit_url_byID()
    #connect_cve2commit_bugzilla()
    '''
    #connect_cve2commit_github('.*?://github.com/Quagga/quagga/commits/.*')
    #connect_cve2commit_cve()







