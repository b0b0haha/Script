#!/usr/bin/python
# -*- coding: UTF-8 -*-

import MySQLdb
import time
import random
import re
import timeit

"""
    Configure settings
"""
DB_IP='172.18.100.15'
DB_NAME='_github_crawler'
DB_VM_NAME='db_sf_338'
DB_USER='github_crawler'
DB_PASS ='github_crawler'

"""
    connect to database
    Parameters:
        db_ip, ip address of database
        db_user, username of database
        db_pass, password of database
        db_name, name of database
    Return:
        a handle of the connected database if success
        or None
"""
def connect_to_db(db_ip,db_user,db_pass,db_name):
    try:
        start = timeit.default_timer()
        db = MySQLdb.connect(db_ip,db_user,db_pass,db_name)
        db.set_character_set('utf8')
        end = timeit.default_timer()
        print('connect time: '+str(end-start))
        if(db == None):
            return None
    
        return db
    except Exception as e:
        print e
        return None


"""
    Connect to database with default setting
    Parameters:
    Return:
        a handle of the connected database if success
        or None
"""
def connect_to_db_simple():
    db = None
    count = 5
    while True:
        count = count - 1
        db = connect_to_db(DB_IP,DB_USER,DB_PASS,DB_NAME)
        if db is not None or count < 0:
            break

        random.seed()
        time.sleep(random.randint(1, 5))
    return db



def query_raw_bytes():
    try:

        conn = connect_to_db_simple()
        sql = "select function, rawA, rawB, sizeA_ori, sizeB_ori, similarity from Function_Raw_FileUnit where sizeA_ori > 20 order by sizeA_ori DESC limit 0, 100;"
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()

        #print result[0]
        if len(result) > 0:
            return result

        return []
    except Exception, e:
        print e
        return []

#============================ for get the func2bin===========================================#
def query_fileID_by_fun(path,functiom_name):
    try:
        conn=connect_to_db_simple()
        sql="select debug_file from S_ImageMagick_Src2Bin where source_file = '%s' and function_name = '%s';" % (path, functiom_name)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
    # print result[0]
        if len(result) > 0:
          return result
        return []

    except Exception, e:
        print e
        return []

def query_filepath_by_fileID(debug_file, commit_id):
    try:
        conn=connect_to_db_simple()
        sql="select local_url from S_ImageMagick_Bin where id = '%s' and tag = '%s';" %(str(debug_file), str(commit_id))
        cursor=conn.cursor()
        cursor.execute(sql)
        result=cursor.fetchall()
        conn.close()
        if len(result)>0:
            url_r = result[0]
            url = url_r[0]
            return url
        return None
    except Exception, e:
        print e
        return None


#============================for  compiling the ImageMagick commit-version===================#

def get_commit_version():
    try:
        conn = connect_to_db_simple()
        sql = "select commit, local_url from Security_Commit_Snapshot"
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        if len(result) > 0:
            return result
        
        return []

    except Exception, e:
        print e
        return []


def add_ImageMagick_bin(uri, filename, tag):
    try:
        conn = connect_to_db_simple()
        cursor = conn.cursor()

        sql = "select id from S_ImageMagick_Bin where tag = '%s' and filename = '%s';" % (tag, filename)
        cursor.execute(sql)
        result = cursor.fetchall()
        # print result
        if len(result) > 0:
            # sql = "update Diff_Files set bindiff_file_local_url = '%s' where binary_A = %d && binary_B = %d;"\
            # %(diff_local_url, binary_A, binary_B)
            # cursor.execute(sql)
            # db.commit()
            conn.close()
            return 0

        sql = "insert into S_ImageMagick_Bin (local_url, filename, tag) values ('%s', '%s', '%s');" \
              % (uri, filename, tag)
        cursor.execute(sql)

        conn.commit()

        conn.close()

        # sql = "select id from U_File_Debug where built_file = %d and built_sym_file = %d and buildid = '%s';"%(code_packid, dbg_packid, buildid)
        # cursor.execute(sql)

        # result = cursor.fetchall()
        # print result

        # if result is not None and len(result) != 0:
        #    return int(result[0][0])

        return 0
    except Exception, e:
        print e
        return -1


def add_ImageMagick_compile_src2bin(conn, function_addr, symbol_type, function_name, source_file, source_lineno, debug_file):
    try:
        # conn = connect_to_db_simple()
        cursor = conn.cursor()
        '''
        sql = "select id from S_ImageMagick_Src2Bin where debug_file = %d and function_address = '%s' and function_name = '%s';" % (
        debug_file, function_addr, function_name)
        cursor.execute(sql)
        result = cursor.fetchall()
        # print result
        if len(result) > 0:
            # sql = "update Diff_Files set bindiff_file_local_url = '%s' where binary_A = %d && binary_B = %d;"\
            # %(diff_local_url, binary_A, binary_B)
            # cursor.execute(sql)
            # db.commit()
            # conn.close()
            return 0
        '''
        sql = "insert into S_ImageMagick_Src2Bin (debug_file, function_address, function_name, symbol_type, source_file, source_lineno) values (%d, '%s', '%s', '%s', '%s', %d);" \
              % (debug_file, function_addr, function_name, symbol_type, source_file, source_lineno)
        cursor.execute(sql)

        conn.commit()

        # conn.close()
        return 1
    except Exception, e:
        print 'db operation failed for saving bin2src record [Exception]', e
        return -1

def query_ImageMagick_compile_files(start, limit):
    try:
        conn = connect_to_db_simple()
        #conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "SELECT id, local_url, filename, tag FROM `S_ImageMagick_Bin` limit %d, %d;"%(start, limit)
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return result

        return []

    except Exception as e:
        print e
        return []
def query_ImageMagick_processed_compile_files():
    try:
        conn = connect_to_db_simple()
        #conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "SELECT distinct debug_file FROM `S_ImageMagick_Src2Bin`;"
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return [int(x) for (x,) in result]

        return []

    except Exception as e:
        print e
        return []
#==========================================for commit&version========================================#

def add_commit_version(local_url, commit, repo):
    try:
        conn = connect_to_db_simple()
        cursor = conn.cursor()
        sql = "select id from Security_Commit_Snapshot where repository = %d and commit = '%s';"%(repo, commit)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) > 0:
            return True


        sql = "insert into Security_Commit_Snapshot (repository, local_url, commit) values\
         (%d, '%s', '%s');"%(repo, local_url, commit)
        cursor.execute(sql)
        conn.commit()

        conn.close()

        return True
    except Exception as e:
        print e
        return False


def query_commits_of_snapshots(repo):
    try:

        conn = connect_to_db_simple()
        sql = "select commit from Security_Commit_Snapshot where repository=%d;"%(repo)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()

        #print result[0]
        if len(result) == 1:
            return [result[0][0]]
        elif len(result) > 1:
            #print result
            commits = [x for (x,) in result]
            #print 'commits', commits
            return commits

        return []
    except Exception as e:
        print e
        return []

#====================================================================================================#


#==========================================for parsing commit parentship==============================#

def query_commit_parents(commit,conn):
    try:

        sql = "select parent from Commit_Parentship where child like '%s';"%(commit)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()

        #print result[0]
        if len(result) == 1:
            return [result[0][0]]
        elif len(result) > 1:
            #print result
            commits = [x for (x,) in result]
            #print 'commits', commits
            return commits

        return []
    except Exception as e:
        print e
        return []

def query_tags(repo):
    try:

        conn = connect_to_db_simple()
        sql = "select name, commit from Tag where repository = %d;"%(repo)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()

        #print result[0]
        if len(result) > 0:
            return result

        return []
    except Exception, e:
        print e
        return []

def add_commit_tag(repo, commit, tag):
    try:
        conn = connect_to_db_simple()
        cursor = conn.cursor()
        sql = "select id from Tag_Commit where repository = %d and tag = '%s' and commit = '%s';"%(repo, tag, commit)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) > 0:
            return True
        

        sql = "insert into Tag_Commit (repository, tag, commit) values\
         (%d, '%s', '%s');"%(repo, tag, commit)
        cursor.execute(sql)
        conn.commit()

        conn.close()

        return True
    except Exception as e:
        print e
        return False

#=====================================================================================================#


#=====================================for commit2mongo================================================#

def query_repo_commits(repo,conn):
    try:


        start = timeit.default_timer()
        sql = "select sha, author, committer, stats_additions, stats_deletions, stats_total from Commit where repository = %d;"%(repo)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        end = timeit.default_timer()
        print('query time: '+ str(end-start))


        #print result[0]
        if len(result) > 0:
            return result

        return []
    except Exception, e:
        print e
        return []

def query_nameduser(user_id,conn):
    try:
        sql = "select id, login, name, email, created_at, updated_at, type, location, bio, blog, company, followers, following, public_repos from NamedUser where id = %d;"%(user_id)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        #print result[0]
        if len(result) > 0:
            nu = {}
            nu['id'] = int(result[0][0])
            nu['login'] = result[0][1]
            nu['name'] = result[0][2]
            nu['email'] = result[0][3]
            nu['created_at'] = result[0][4]
            nu['update_at'] = result[0][5]
            nu['type'] = result[0][6]
            nu['location'] = result[0][7]
            nu['bio'] = result[0][8]
            nu['blog'] = result[0][9]
            nu['company'] = result[0][10]
            nu['followers'] = int(result[0][11])
            nu['following'] = int(result[0][12])
            nu['public_repos'] = int(result[0][13])
            return nu

        return None
    except Exception, e:
        print e
        return None

def query_commit_tag(repo, commit,conn):
    try:

        sql = "select tag from Tag_Commit where repository= %d and commit = '%s';"%(repo, commit)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()

        #print result[0]
        if len(result) > 0:
            return [x for (x,) in result]

        return None
    except Exception, e:
        print e
        return None

def query_commit_files(commit,conn):
    try:
        start = timeit.default_timer()
        sql = "select sha, filename, previous_filename, status, additions, deletions, changes, patch_local_url from CommitFile where commit = '%s';"%(commit)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        end = timeit.default_timer()
        print('query time:'+str(end-start))
        #print result[0]
        if len(result) > 0:
            return result

        return []
    except Exception, e:
        print e
        return []

def query_gitcommit(commit,conn):
    try:

        sql = "select message, author_name, author_email, author_date, committer_name, committer_email, committer_date from GitCommit where sha = '%s';"%(commit)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()

        #print result[0]
        if len(result) > 0:
            gitcommit = {}
            gitcommit['message'] = result[0][0]
            gitcommit['author'] = {'name':result[0][1], 'email':result[0][2], 'date':result[0][3]}
            gitcommit['committer'] = {'name':result[0][4], 'email':result[0][5], 'date':result[0][6]}
            return gitcommit

        return None
    except Exception, e:
        print e
        return None

#=====================================================================================================#


#====================================for compile========================================================#

def query_compile_tags(repo):
    try:
        conn = connect_to_db_simple()

        cursor = conn.cursor()

        sql = "select name, zipball_local_url from Security_Commit_Snapshot where repository = %d;"%(repo)
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            #print 'larger than 1', result
            return result

        return []

    except Exception as e:
        print e
        return []

def query_processed_compile_files():
    try:
        conn = connect_to_db_simple()
        #conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "SELECT distinct debug_file FROM `S_FFmpeg_Src2Bin`;"
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return [int(x) for (x,) in result]

        return []

    except Exception as e:
        print e
        return []


def query_compile_files():
    try:
        conn = connect_to_db_simple()
        #conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "SELECT id, local_url, filename, tag FROM `S_FFmpeg_Bin`;"
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return result

        return []

    except Exception as e:
        print e
        return []


def add_ffmpeg_bin(uri, filename, tag):
    try:
        conn = connect_to_db_simple()
        cursor = conn.cursor()

        sql = "select id from S_FFmpeg_Bin where tag = '%s' and filename = '%s';"%(tag, filename)
        cursor.execute(sql)
        result = cursor.fetchall()
        #print result
        if len(result) > 0:
            #sql = "update Diff_Files set bindiff_file_local_url = '%s' where binary_A = %d && binary_B = %d;"\
            #%(diff_local_url, binary_A, binary_B)
            #cursor.execute(sql)
            #db.commit()
            conn.close()
            return 0

        sql = "insert into S_FFmpeg_Bin (local_url, filename, tag) values ('%s', '%s', '%s');"\
                %(uri, filename, tag)
        cursor.execute(sql)

        conn.commit()

        conn.close()

        #sql = "select id from U_File_Debug where built_file = %d and built_sym_file = %d and buildid = '%s';"%(code_packid, dbg_packid, buildid)
        #cursor.execute(sql)

        #result = cursor.fetchall()
        #print result

        #if result is not None and len(result) != 0:
        #    return int(result[0][0])

        return 0
    except Exception, e:
        print e
        return -1


def add_compile_src2bin(conn, function_addr, symbol_type, function_name, source_file, source_lineno, debug_file):
    try:
        #conn = connect_to_db_simple()
        cursor = conn.cursor()

        sql = "select id from S_FFmpeg_Src2Bin where debug_file = %d and function_address = '%s' and function_name = '%s';"%(debug_file, function_addr, function_name)
        cursor.execute(sql)
        result = cursor.fetchall()
        #print result
        if len(result) > 0:
            #sql = "update Diff_Files set bindiff_file_local_url = '%s' where binary_A = %d && binary_B = %d;"\
            #%(diff_local_url, binary_A, binary_B)
            #cursor.execute(sql)
            #db.commit()
            #conn.close()
            return 0

        sql = "insert into S_FFmpeg_Src2Bin (debug_file, function_address, function_name, symbol_type, source_file, source_lineno) values (%d, '%s', '%s', '%s', '%s', %d);"\
                %(debug_file, function_addr, function_name, symbol_type, source_file, source_lineno)
        cursor.execute(sql)

        conn.commit()

        #conn.close()
        return 1
    except Exception, e:
        print 'db operation failed for saving bin2src record [Exception]', e
        return -1
    

#=======================================================================================================#


#====================================for launchpad ubuntu===============================================#

def query_all_dbgsym():
    try:
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "select id, build, filename, local_url from U_Built_File where filename like '%%.ddeb' order by build DESC;"
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return result

        return []

    except Exception as e:
        print e
        return []


def query_processed_dbgsym():
    try:
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "select distinct built_sym_file from U_File_Debug;"
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return result

        return []

    except Exception as e:
        print e
        return []


def query_one_code_pack(build_id, code_packname):
    try:
        #print build_id, code_packname
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "select id, build, filename, local_url from U_Built_File where filename like '%s' and build = %d;"%(code_packname, build_id)
        #print sql
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return result[0]

        return None

    except Exception as e:
        print e
        return None

def add_one_unstripped_file(code_packid, dbg_packid, uri, filename, buildid):
    try:
        #conn = connect_to_db_simple()
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')
        cursor = conn.cursor()

        sql = "select id from U_File_Debug where built_file = %d and built_sym_file = %d and buildid = '%s';"%(code_packid, dbg_packid, buildid)
        cursor.execute(sql)
        result = cursor.fetchall()
        #print result
        if len(result) > 0:
            #sql = "update Diff_Files set bindiff_file_local_url = '%s' where binary_A = %d && binary_B = %d;"\
            #%(diff_local_url, binary_A, binary_B)
            #cursor.execute(sql)
            #db.commit()
            conn.close()
            return 0

        sql = "insert into U_File_Debug (built_file, built_sym_file, filename, buildid, unstripped_local_url) values (%d, %d, '%s', '%s', '%s');"\
                %(code_packid, dbg_packid, filename, buildid, uri)
        cursor.execute(sql)

        conn.commit()

        conn.close()

        #sql = "select id from U_File_Debug where built_file = %d and built_sym_file = %d and buildid = '%s';"%(code_packid, dbg_packid, buildid)
        #cursor.execute(sql)

        #result = cursor.fetchall()
        #print result

        #if result is not None and len(result) != 0:
        #    return int(result[0][0])

        return 0
    except Exception, e:
        print e
        return -1

#=======================================================================================================#


#====================================for statis=========================================================#

def query_all_debug_files():
    try:
        #conn = connect_to_db_simple()
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "SELECT D.id, D.filename, D.unstripped_local_url FROM `U_Build` as A, U_Source_Package as B, U_Built_File as C, U_File_Debug as D where A.arch like '%s' and A.package = B.id and B.name like '%s' and C.build = A.id and D.built_file = C.id;"%('i386', 'ffmpeg')

        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return result

        return []

    except Exception as e:
        print e
        return []


def query_processed_debug_files():
    try:
        #conn = connect_to_db_simple()
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        cursor = conn.cursor()

        sql = "SELECT distinct debug_file FROM `S_FFmpeg_Bin2Src`;"
        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if len(result) > 0:
            return [int(x) for (x,) in result]

        return []

    except Exception as e:
        print e
        return []


def save_bin2src_record(conn, function_addr, symbol_type, function_name, source_file, source_lineno, debug_file):
    try:
        #conn = connect_to_db_simple()
        cursor = conn.cursor()

        sql = "select id from S_FFmpeg_Bin2Src where debug_file = %d and function_address = '%s' and function_name = '%s';"%(debug_file, function_addr, function_name)
        cursor.execute(sql)
        result = cursor.fetchall()
        #print result
        if len(result) > 0:
            #sql = "update Diff_Files set bindiff_file_local_url = '%s' where binary_A = %d && binary_B = %d;"\
            #%(diff_local_url, binary_A, binary_B)
            #cursor.execute(sql)
            #db.commit()
            #conn.close()
            return 0

        sql = "insert into S_FFmpeg_Bin2Src (debug_file, function_address, function_name, symbol_type, source_file, source_lineno) values (%d, '%s', '%s', '%s', '%s', %d);"\
                %(debug_file, function_addr, function_name, symbol_type, source_file, source_lineno)
        cursor.execute(sql)

        conn.commit()

        #conn.close()
        return 1
    except Exception, e:
        print 'db operation failed for saving bin2src record [Exception]', e
        return -1


#=======================================================================================================#

#============================================parse buildlog================================================#
def query_all_buildlog():
    try:
        #conn = connect_to_db_simple()
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        sql = "select id, buildlog_local_url from U_Build where buildlog_local_url != 'None';"
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()

        if len(result) > 0:
            return result

        return []
    except Exception as e:
        print(e)
        return []

def query_all_processed_buildlog():
    try:
        #conn = connect_to_db_simple()
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        sql = "select build from U_Build_Option;"
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()

        if len(result) > 0:
            return [x for (x, ) in result]

        return []
    except Exception as e:
        print(e)
        return []


def add_one_build_option(build, kernel, toolchain, vendors, versions, optimizations):
    try:
        #conn = connect_to_db_simple()
        conn = connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')

        sql = "insert into U_Build_Option(build, kernel, toolchain, compiler_vendor, compiler_version, optimization) values \
            (%d, '%s', '%s', '%s', '%s', '%s');"%(build, kernel, toolchain, vendors, versions, optimizations)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()

        #sql = "select id from Ubuntu_Package where dbgsym_name='%s' and system like 'Ubuntu 12.04%%';"%(dbgsym_package)
        #cursor.execute(sql)
        #result = cursor.fetchall()

        conn.close()

        #if len(result) > 0:
        #    print(result[0])
        #    return int(result[0][0])

        return 0
    except Exception as e:
        print(e)
        return -1


#==========================================================================================================#

def select_suffix_words():
    try:
        conn = connect_to_db_simple()

        sql = "select suffix from SeedFile;"

        cursor = conn.cursor()

        cursor.execute(sql)

        result = cursor.fetchall()

        conn.close()

        string = ""

        print result[0]

        with open("suffies.txt", "w") as f:
            prog = re.compile("[a-zA-Z0-9]+$")
            for suffix in result:
                if prog.match(suffix[0]):
                    #string = string + " " + suffix[0]
                    f.write(suffix[0] + " ")
        
    except Exception as e:
        print e
        return None

def select_files_by_suffix(suffix):
    try:
        
        conn = connect_to_db_simple()

        sql = "select id, filename, local_url from SeedFile where suffix like '%s' and size < 10000 limit 0, 10000;"%(suffix)

        cursor = conn.cursor()

        cursor.execute(sql)

        result = cursor.fetchall()

        conn.close()

        #print result[0]

        return result

        return True
    except Exception as e:
        print e
        return []


"""
    Add one SeedFile record
    Parameters:
        db, database connection
        filename: original filename
        local_url: index uri in CommonStorage
        suffix: file extension name
        repository: id of a repository which the file belongs to
        size: size of the file in Kbytes
    Return:
        status, True if success otherwise False
"""
def add_one_seedfile_record(db, filename, local_url, suffix, repository, size):
    try:
        cursor = db.cursor()

        sql = "insert into SeedFile (filename, local_url, suffix, repository, size) values\
         ('%s', '%s', '%s', %d, %f);"%(filename, local_url, suffix, repository, size)

        cursor.execute(sql)

        db.commit()

        return True
    except Exception as e:
        print e
        return False

"""
    Select all repositories from one view which is queried by 'varas_timestamp'
    Parameters:
        view, view name
    Return:
        list of a turple (id, name, archive_local_url) or None
"""
def select_all_repos_from_view(view):
    try:
        db = connect_to_db_simple()
        cursor = db.cursor()

        sql = "select %s.id, %s.name, %s.archive_local_url from %s where %s.archive_local_url is not NULL limit 20000, 20010;"%(view,view, view, view, view)

        print sql 
        #sql = "select %s.id, %s.name, %s.archive_local_url from %s where %s.archive_local_url is not NULL and %s.id not in \
        #(select repository from SeedFile);"%(view,view, view, view, view, view)
        #sql = "select %s.id, %s.name, %s.archive_local_url from %s where %s.archive_local_url is not NULL\
        #;"%(view, view, view, view, view)        

        #print sql
        cursor.execute(sql)

        result = cursor.fetchall()

        db.close()

        print result[0]

        if len(result) > 0:
            return result

        return None
    except Exception as e:
        print e
        return None


def select_all_processed_repos():
    try:
        db = connect_to_db_simple()

        sql = "select distinct repository from SeedFile;"

        cursor = db.cursor()

        cursor.execute(sql)

        result = cursor.fetchall()

        db.close()

        if len(result) > 0:
            repos = []
            for r in result:
                repos.append(int(r[0]))
            return repos

        return None

    except Exception as e:
        print e
        return None



"""
    Create view used for parallel control
    Parameters:
        db, database connection
        table, table name which the view will be generated from
    Return:
        new view name or None
"""
def create_temp_view(db, table):
    try:
        
        view_name = "temp_" + str(int(time.time()))
        sql = "create view " + view_name + " as select id from %s;"%(table)
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()

        return view_name
    except Exception as e:
        print e
        return None


"""
    Delete one record from a tempview
    Parameters:
        db, database connection
        view, view name
        id, index of the record will be deleted
    Return:
        status, True if success otherwise False
"""
def delete_record_from_tempview(db, view, id):
    try:
        
        if not isinstance(id, str):
            sql = "delete from %s where id=%d;"%(view, id)
        else:
            sql = "delete from %s where id='%s';"%(view, id)
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()

        return True
    except Exception as e:
        print e
        return False


def count_of_view(db, view):
    try:
        sql = "select count(*) from %s;"%(view)
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()

        print result

        return int(result[0][0])
    except Exception as e:
        print e
        return None

"""
    Decide whether one record exists in a view
    Parameters:
        db, database connection
        view, view name
        id, index of the record
    Return:
        True if exists otherwise False
"""
def is_exist_in_tempview(db, view, id):
    try:
        if not isinstance(id, str):
            sql = "select * from %s where id=%d;"%(view, id)
        else:
            sql = "select * from %s where id='%s';"%(view, id)

        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()

        if len(result) > 0:
            return True
        
        return False
    except Exception as e:
        print e
        return True


"""
    Select binaries which are compiled from one version (Tag)
    Parameters:
        db, an open database connection
        tag_commit, commit index of the given tag
    Return:
        list of queried entry if success, otherwise None 
"""
def select_binaries_of_one_tag(db, tag_commit):
    try:
        
        sql = "select id, binary_local_url, binary_name, order from Compiled_Binary where tag = '%s';"%(tag_commit)

        cursor = db.cursor()

        cursor.execute(sql)
        result == cursor.fetchall()

        print result
        return result

    except Exception as e:
        print e
        return None



"""
    Query all bianries compiled from all versions of the given repository
    Parameters:
        db, an open database connection
        repo, id of a given repository
    Return:
        list of all queried entries if success, otherwise None
"""
def select_all_binaries_of_one_repo(db, repo):
    try:
        sql = "select id, binary_local_url, binary_name, sequence_no from Compiled_Binary where tag in \
                  (select commit from Tag where repository = %d) limit 0,10;"%(repo)

        cursor = db.cursor()
        
        cursor.execute(sql)
        result = cursor.fetchall()

        #print result[0]
        return result

    except Exception as e:
        print e
        return None



def update_binary_record(db, field_name, field_value, id):
    try:
        sql = "update Compiled_Binary set %s = '%s' where id = %d;"%(field_name, field_value, id)

        cursor = db.cursor()
        cursor.execute(sql)

        db.commit()

        return True
    except Exception as e:
        print e
        return False


"""
    Add one Diff_Files record
    Parameters:
        db, a database connection
        binary_A, identifier of previous version A in table Compiled_Binary
        binary_B, identifier of post version B in table Compiled_Binary
        diff_local_url, index of .BinDiff file stored in CommonStorage
    Return:
        id of the new added record if success
        -1 if fail
"""
def add_one_diff_files_record(db, binary_A, binary_B, diff_local_url):
    try:
        
        cursor = db.cursor()

        sql = "select id from Diff_Files where binary_A = %d && binary_B = %d;"%(binary_A, binary_B)
        cursor.execute(sql)
        result = cursor.fetchall()
        print result
        if len(result) > 0:
            sql = "update Diff_Files set bindiff_file_local_url = '%s' where binary_A = %d && binary_B = %d;"\
            %(diff_local_url, binary_A, binary_B)
            cursor.execute(sql)
            db.commit()

            return int(result[0][0])

        sql = "insert into Diff_Files (binary_A, binary_B, bindiff_file_local_url) values (%d, %d, '%s');"\
                %(binary_A, binary_B, diff_local_url)
        cursor.execute(sql)

        db.commit()

        sql = "select id from Diff_Files where binary_A = %d && binary_B = %d;"%(binary_A, binary_B)
        cursor.execute(sql)
        
        result = cursor.fetchall()
        print result

        if result is not None and len(result) != 0:
            return int(result[0][0])

        return -1    

    except Exception as e:
        print e
        return -1


def is_exist_such_diff_function(db, bindiff_id, address1, address2):
    try:
        
        cursor = db.cursor()

        sql = "select id from Diff_Function where bindiff = %d and functionA_addr = %d \
        and functionB_addr = %d;"%(bindiff_id, address1, address2)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) > 0:
            return True

        return False
    except Exception as e:
        print e
        return False


def add_one_diff_function_record(db, bindiff_id, name1, name2, address1, address2, bytefile1, \
    bytefile2, asmfile1, asmfile2, jpegfile1, jpegfile2, similarity, confidence, algorithm):
    try:
        cursor = db.cursor()

        '''
        sql = "select id from Diff_Function where bindiff = %d and functionA_addr = %d \
        and functionB_addr = %d;"%(bindiff_id, address1, address2)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) > 0:
            return True
        '''
        
        sql = "insert into Diff_Function (bindiff, functionA_name, functionB_name, \
        functionA_addr, functionB_addr, functionA_raw, functionB_raw, \
        functionA_asm, functionB_asm, functionA_grayscale, functionB_grayscale, \
        similarity, confidence, match_algorithm) values (%d, '%s', '%s', %d, %d, \
        '%s', '%s', '%s', '%s', '%s', '%s', %f, %f, %d);"%(bindiff_id, \
        name1, name2, address1, address2, bytefile1, bytefile2, \
        asmfile1, asmfile2, jpegfile1, jpegfile2, similarity, confidence, algorithm)

        cursor.execute(sql)

        db.commit()

        return True
    except Exception as e:
        print e
        return False


#=============================================================#
#select one field value from  table
#@para db, database pointer
#@para table_name, table name
#@para field_name, the name of indexed field,
#       value is static_dot_uri or static_path_image_uri
#@para r_id, index a record
#@return value of indexed field
#=============================================================#
def select_field_from_table(db, table_name, field_name, r_id):
    cursor = db.cursor()
    
    sql="select %s from %s where id = %s;"%(field_name, table_name, r_id)
    
    try:
       cursor.execute(sql)
       result=cursor.fetchall()
       result=str(result[0])
       result=result.split('(')[1].split(',')[0]

    except Exception,e:
        print "error to task table:",e
        return ''

    return result

def select_field_by_vmip(db,table_name,field_name,ip):
    cursor=db.cursor()
    sql="select %s from %s where vm_ip = '%s';"%(field_name,table_name,ip)

    print sql
    try:
       cursor.execute(sql)
       result=cursor.fetchall()
       if(len(result)>0):
           result=str(result[0])
           result=result.split('(')[1].split(',')[0]
       else:
            result=''
    except Exception,e:
        print "error to task table:",e
        return ''

    return result

#=========================================================#
#insert a record with field=value
#@para db, db handle
#@para field, field name
#@para value, field value
#=========================================================#
def insert_into_db(db,table_name,field,value):
    cursor = db.cursor()
    sql="insert into %s (%s) values ('%s');"%(table_name,field,value)
    #print sql

    try:
        cursor.execute(sql)
    except Exception,e:
        print 'some exception has happened when insert into db',e
        return


#========================================================#
#update a record with field=value
#@para db, db handle
#@para table_name, table name
#@para field, field name
#@para value, field value
#@para r_id, index of record
#========================================================#
def update_one_record(db,table_name,field,value,r_id):
    cursor=db.cursor()
    sql="update %s set %s = '%s' where id = %s;"%(table_name,field,value,r_id)

    #print sql
    try:
        cursor.execute(sql)
    except Exception,e:
        print 'some exception has happened when update db',e
        return

#==========================================================#
#update table 'vm' by ip address
#==========================================================#
def update_one_vm(db,table_name,field,value,ip):
    cursor=db.cursor()
    sql="update %s set %s = '%s' where vm_ip = '%s';"%(table_name,field,value,ip)
    #print sql
    try:
        cursor.execute(sql)
    except Exception,e:
        print 'some exception has happened when update db',e
        return

    
#===========================================================#
#update a record in task table with new values of dot&svg uris
#@para db, handle of db
#@para r_id, index of a record
#@para dot_uri, uri of static call graph dot file
#@para svg_uri, uri of static call svg file
#===========================================================#
def update_one_record_simple(db,r_id,dot_uri,svg_uri):
    cursor=db.cursor()
    sql="update %s set %s = '%s', %s = '%s' where id = %s;"%(TABLE_TASK_NAME,FN_S_DOT_URI,dot_uri,FN_S_SVG_URI,svg_uri,r_id)

    #print sql
    try:
        cursor.execute(sql)
    except Exception,e:
        print 'some exception has happened when update db',e
        return



#============================================================#
#db=connect_to_db(DB_IP,DB_USER,DB_PASS,DB_NAME)
#
#if(db == None):
#    print 'connect to db error'
#else:
#    result=select_field_from_table(db,TABLE_TASK_NAME,"static_dot_uri",338)
#    #print select_field_from_table(db,TABLE_TASK_NAME,"")
#    print result
#    db.close()
#
#==================================================================#
#db=connect_to_db(DB_IP,DB_USER,DB_PASS,DB_NAME)
#if (db == None):
#    print 'failed to connect to db'
#else:
#    #insert_into_db(db,'dynamic_dot_uri','20bd793e141d9b5967f1061f483b27eb')
#    #update_one_record(db,'dynamic_dot_uri','44ffbad6fe4adbb347a67fa87ffafab9',1)
#    update_one_record_simple(db,338,'30f714a740a51560f0fda4513eedfa23','601197cff878760874ea019cea30e4a1')
#    db.close()
#==================================================================#

'''
db = connect_to_db_simple()

select_all_binaries_of_one_repo(db, 680471)

update_binary_record(db, 'binexport_local_url', 'vim-v70d4-gcc-g-o2.BinExport', 9)

db.close()
'''
if __name__ =='__main__':
    db = connect_to_db_simple()
 





