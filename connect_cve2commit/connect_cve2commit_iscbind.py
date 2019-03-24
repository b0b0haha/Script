import pymongo
import re
import requests
import os
from pyquery.pyquery import PyQuery as pq
import xlwt
PROJECT_NAME='iscbind'
HOST = '172.18.108.169'
PORT =21087
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
    file_path = os.path.join(os.getcwd(), PROJECT_NAME+'-refs.txt')
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
            #print(gitmessage)
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
                        count += 1
                        print(re_result.group(1), url)
                        if db.cve_commit.find({'cve': ref['cve'], 'commit': commit['_id']}).count() == 0:
                            cve_commit = {}
                            cve_commit['cve'] = ref['cve']
                            cve_commit['commit'] = commit['_id']
                            cve_commit['patch_version'] = None
                            db.cve_commit.insert_one(cve_commit)


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
def get_secuity_commit(type,pattern):
    #根据特定的正则表达式获取安全相关的commit
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
    re_rules =client.quagga.re_rule.find({})
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
def connect_cve2commit_url_byID(host,flag):
    res= db.ref_str.find({'host':host})
    urls = res[0]['url']
    for url in urls:
        if flag ==1:
            # 直接匹配末尾的内容
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
        elif flag ==2:
            # 匹配链接末尾ID
            result = re.search('[\d]+', str(url.split('=')[-1]))
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
        else:
            # 直接匹配commitID
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
def connect_cve2commit_url():
    refs = db.refs.find({'host':'ftp.isc.org'})
    for ref in refs:
        url= ref['ref']
        text = ref['text']
        commit_result = db.commit.find({'gitcommit.message_t': {'$regex': url, '$options': 'i'}})
        if commit_result.count()!=0:
            print(url)
            print(commit_result.count())
def connect_by_person(cve,commit,version):
    cve_commit = {}
    cve_commit['cve'] = cve
    cve_commit['commit'] = commit
    cve_commit['patch_version'] = version
    if db.cve_commit.find({'cve':cve,'commit':commit}).count()==0:
        db.cve_commit.insert_one(cve_commit)
    else:
        conn = db.cve_commit.find_one({'cve':cve,'commit':commit})
        if conn !=None:
            conn['patch_version']=version
            db.cve_commit.update({'cve':cve,'commit':commit},conn)
def filter_commit():
    cve_list= db.cve_commit_unique.find({})
    for cve in cve_list:
        id = cve['cve']
        shas = cve['commit']
        for sha in shas:
            flag =False
            commit = db.commit.find_one({'_id':sha})
            files = commit['files']
            refiles =''
            for file in files:
                filename = file['filename']
                pattern = re.compile('.*\.c$|h$')
                result = re.match(pattern,filename)
                if result!=None:
                    flag = True
                    print('ok: ',filename)
                    break
                else:
                    refiles+=filename+','
                    print('fail',filename)
            if flag == False:
                print(refiles)
                confirm_by_person(id,sha,'Change/Readme文件增加了关于cve的说明')
def confirm_by_person(cve,commit,reason):
    '''
    手动去除非正确的cve_commit的关联
    :param cve:
    :param commit:
    :param reason:
    :return:
    '''
    condition = {'cve':cve,'commit':commit}
    result_1 = db.cve_commit_meta.delete_one(condition)
    result_2 = db.cve_commit.delete_one(condition)
    print('result_1: '+str(result_1))
    print('result_2: ' + str(result_2))
    condition = {'cve':cve}
    cve_commit_unique = db.cve_commit_unique.find_one(condition)
    commits= cve_commit_unique['commit']
    commits.remove(commit)
    cve_commit_unique['commit']=commits
    result =  db.cve_commit_unique.update(condition,cve_commit_unique)
    print(result)
    cve_comm={}
    cve_comm['cve'] = cve
    cve_comm['commit'] = commit
    cve_comm['patch_version'] = None
    cve_comm['reason'] = reason
    if db.unconfirmed_cve_commit.find({'cve': cve, 'commit': commit}).count() == 0:
        print(cve_comm)
        db.unconfirmed_cve_commit.insert_one(cve_comm)
    if len(commits) == 0:
        db.cve_commit_unique.delete_one(condition)
        return
def add_file2commit():
    '''
    从git_commit中添加file信息到cve_commit_meta
    :return:
    '''
    cve_commits= db.cve_commit_meta.find({})
    count =0
    conn ={}
    db.cve_commit_meta_1.remove({})
    for cve_commit in cve_commits:
        commit = cve_commit['commit']
        conn['commit']=cve_commit['commit']
        conn['cve']=cve_commit['cve']
        conn['parent_commits']=cve_commit['parent_commits']
        conn['vuln_type']=cve_commit['vuln_type']
        conn['version']=cve_commit['version']
        conn['patch_version']=cve_commit['patch_version']
        git_commit = db.git_commit.find_one({'_id':commit})
        if (git_commit!=None and 'files' in git_commit):
            #db.cve_commit_meta.remove({'cve':cve_commit['cve'],'commit':cve_commit['commit']})
            conn['files']=git_commit['files']
            count+=1
            conn['_id'] = count
            db.cve_commit_meta_1.insert_one(conn)
    print(count)

def get_cve_commit_meta():
    '''
    获取归纳总结的表格
    :return:
    '''
    if os.path.exists('data_cve.xsl'):
        os.remove('data_cve.xsl')
    workbook = xlwt.Workbook()  # 注意Workbook的开头W要大写
    sheet1 = workbook.add_sheet('sheet1', cell_overwrite_ok=True)
    sheet1.write(0,0,'cve')
    sheet1.write(0,1,'vuln_type')
    sheet1.write(0, 2, 'reason')
    sheet1.write(0, 3, 'version')
    sheet1.write(0, 4, 'patch_version')
    sheet1.write(0, 5, 'commit')
    sheet1.write(0, 6, 'files')
    sheet1.write(0, 7, 'diff')
    cve_commits = db.cve_commit_meta_1.find({})
    db.cve_commit_meta_2.remove({})
    count=1
    for cve_commit in cve_commits:
        conn = {}
        conn['cve']=cve_commit['cve']
        conn['vuln_type']=cve_commit['vuln_type']
        git_commit = db.git_commit.find_one({'_id':cve_commit['commit']})
        if git_commit!=None:
            conn['reason']=git_commit['message']
        else:
            conn['reason']=None
        patch_version =[]
        if cve_commit['version']!='':
            for patch in cve_commit['version']:
                if patch['Product'] == 'Bind' and patch['Vendor'] == 'ISC':
                    version = ''
                    if patch['Update'] != '':
                        version = patch['Version'] + '-' + patch['Update']
                    else:
                        version = patch['Version']
                    patch_version.append(version)
            conn['version'] = ','.join(patch_version)
        else:
            conn['version']=''
        conn['patch_version']=cve_commit['patch_version']
        conn['commit']=cve_commit['commit']
        files =''
        for file in cve_commit['files']:
            if (file['filename'].split('.')[-1].lower() not in ['c', 'cc', 'cpp', 'h', 'hpp', 'hh']):
                continue
            cfile=''
            cfile+=file['filename']
            print(cfile)
            headings =[]
            if file['chunks_meta']!=None:
                cfile+=':'
                for chunk in file['chunks_meta']:
                    if chunk!=None:
                        heading=str(chunk['heading'])+'@@'+str(chunk['to_lines'])+','+str(chunk['to_lineno'])+' '+str(chunk['from_lines'])+','+str(chunk['from_lineno'])+'@@'
                        headings.append(heading)
            cfile+='|'.join(headings)
            print(cfile)
            files+=cfile
        conn['files']=files
        print(files)
        conn['diff']='https://github.com/isc-projects/bind9/commit/'+conn['commit']+'?diff=split'
        db.cve_commit_meta_2.insert_one(conn)
        sheet1.write(count, 0, conn['cve'])
        sheet1.write(count, 1, conn['vuln_type'])
        sheet1.write(count, 2, conn['reason'])
        sheet1.write(count, 3, conn['version'])
        sheet1.write(count, 4, conn['patch_version'])
        sheet1.write(count, 5, conn['commit'])
        sheet1.write(count, 6, str(conn['files']))
        sheet1.write(count, 7, conn['diff'])
        count+=1
    workbook.save('data_cve.xls')

def get_unconnected_cve():
    db.uncon_cve.remove({})
    cve_meta = db.cve.find({})
    cve_commits = db.cve_commit_meta_2.find({})
    con_cve=[]
    for conn in cve_commits:
        cve = conn['cve']
        con_cve.append(cve)
    for cve in con_cve:
        print(cve)
    for cve in cve_meta:
        if cve['id'] in con_cve:
            continue
        else:
            db.uncon_cve.insert_one(cve)

def add_new_cve(id):
    '''
    人工添加新的cve
    :param id:
    :return:
    '''
    if db.cve_commit_meta_1.find({'cve':id}).count()==0:
        result = db.uncon_cve.find_one({'_id': id})
        if result == None:
            print('not found in uncon_cve')
            cve = client.cve.item_str.find_one({'id': id})
            if cve != None:
                print(cve['id'])
                if db.cve.find_one({'id': cve['id']})==None:
                    print('not found in cve_details')
                    db.cve.insert_one(cve)
                    db.uncon_cve.insert_one(cve)
        else:
            print('found in uncon_cve')

def get_patch_cve():
    '''
    获取每个版本存在的CVE
    :return:
    '''
    cve_commit_metas = db.cve_commit_meta_2.find({})
    db.patch_cve.remove({})
    for conn in cve_commit_metas:
        versions = conn['patch_version'].split(',')
        for version in versions:
            patch = db.patch_cve.find_one({'version':version})
            if patch!=None:
                if conn['cve'] not in patch['cve']:
                    patch['cve'].append(conn['cve'])
                    patch['count'] += 1
                    db.patch_cve.update({'version': version}, patch)
            else:
                patch_cve={}
                patch_cve['version']=version
                patch_cve['cve']=[]
                patch_cve['cve'].append(conn['cve'])
                patch_cve['count']=1
                db.patch_cve.insert_one(patch_cve)
    patch_cves = db.patch_cve.find({}).sort('count',-1)
    workbook = xlwt.Workbook()  # 注意Workbook的开头W要大写
    sheet = workbook.add_sheet('patch_version', cell_overwrite_ok=True)
    sheet.write(0,0,'version')
    sheet.write(0,1,'cve')
    sheet.write(0,2 ,'count')
    count=0
    for patch_cve in patch_cves:
        count+=1
        sheet.write(count,0,patch_cve['version'])
        cves = ','.join(patch_cve['cve'])
        sheet.write(count,1,cves)
        sheet.write(count,2,patch_cve['count'])
    workbook.save('data.xls')

def process_cve_commit():
    '''
    整理cve_commit中commit的格式
    :return:
    '''
    cve_commits = db.cve_commit.find({})
    for conn in cve_commits:
        patch_version = conn['patch_version']
        if patch_version!=None:
            patch_version = re.sub('\s+','',patch_version)
            conn['patch_version'] = patch_version
            db.cve_commit.update({'cve':conn['cve'],'commit':conn['commit']},conn)



if __name__=='__main__':
    #connect_cve2commit_cve()
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
    connect_cve2commit_bugzilla()
    connect_cve2commit_github('.*?://github.com/isc-projects/bind9/commit[s]*/.*')
    '''
    '''
    type='issue|request'
    pattern_str ='(issues*|requests*)[\s]*#'
    get_secuity_commit(type,pattern_str) 
    #get_info('[\s]*dos')
    '''
    '''
    #get_hot_refs(0) 
    #connect_cve2commit_bugzilla()
    '''
    #get_security_commit_db()
    #connect_cve2commit_url_byID()
    #get_info('secunia')
    #connect_by_person('CVE-2016-2848','4adf97c32fcca7d00e5756607fd045f2aab9c3d4')
    #connect_cve2commit_url_byID('downloads.avaya.com',1)
    #connect_cve2commit_url()
    #add_new_cve('CVE-2017-3135')
    #connect_by_person('CVE-2017-3135','b1b5229a474d606a98988dc9cb34bec0e39ab2c5','9.12.0')
    #filter_commit()
    #confirm_by_person('CVE-2016-1286', 'b6dea7aee95416f6229f72b4e7459a2b1b27f256','Change/Readme文件增加了关于cve的说明')
    #add_file2commit()
    get_cve_commit_meta()
    #get_unconnected_cve()
    #get_patch_cve()
    #process_cve_commit()





