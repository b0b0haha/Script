import sys
import os
sys.path.append(os.path.abspath('../utils'))

import subprocess
import db_operation
import udload
import os

def process_with_nm(path):
    try:

        cmd = 'nm -l ' + path
        process = subprocess.Popen(cmd, shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

        # wait for the process to terminate
        out, err = process.communicate()
        errcode = process.returncode
        if errcode != 0:
            return []
        
        lines = out.split('\n')
        print len(lines) 
        records = []
        for line in lines:
            #print line
            #break
            elems = line.split(' ')
            elems = [x for x in elems if x != ''] 
            print len(elems), elems

            addr = None
            sym_type = None
            func_name = None
            src_file = None
            src_lineno = -1


            record = None

            if len(elems) == 2 and elems[0] == 'U':
                if '\t' not in elems[1]:
                    sym_type = elems[0]
                    func_name = elems[1]
                else:
                    sym_type = elems[0]
                    members = elems[1].split('\t')
                    if len(members) == 1:
                        func_name = members[0]
                    else:
                        func_name = members[0]
                        src_file = members[1].split(':')[0]
                        if 'ImageMagick-' in src_file:
                            src_file = '/'.join(src_file.split('ImageMagick-')[1].split('/')[1:])
                            print src_file
                        src_lineno = int(members[1].split(':')[1])
                #record = (addr, sym_type, func_name, src_file, src_lineno)
            elif len(elems) == 3:
                addr = elems[0]
                sym_type = elems[1]
                members = elems[2].split('\t')
                if len(members) == 1:
                    func_name = members[0]
                else:
                    func_name = members[0]
                    src_file = members[1].split(':')[0]
                    if 'ImageMagick-' in src_file:
                        src_file = '/'.join(src_file.split('ImageMagick-')[1].split('/')[1:])
                    src_lineno = int(members[1].split(':')[1])
            elif len(elems) == 0:
                    continue

            record = (addr, sym_type, func_name, src_file, src_lineno)
            records.append(record)
            #print record
            #break
        #print records         
        #print out
        return records
    except Exception, e:
        print 'processing with nm failed [Exception]', e
        return []

def save_to_db(records, bin_file):
    try:
        conn = db_operation.connect_to_db_simple()
        #conn = db_operation.connect_to_db('172.18.100.125', 'lp_crawler', '_lp_crawler', '_launchpad_crawler')
        for (function_addr, symbol_type, function_name, source_file, source_lineno) in records:
            db_operation.add_ImageMagick_compile_src2bin(conn, str(function_addr), str(symbol_type), str(function_name), str(source_file), int(source_lineno), bin_file)

        conn.close()
        return True
    except Exception, e:
        print 'save to db [Exception]', e
        return False

def clean(path):
    try:

        os.remove(path)
        return True
    except Exception, e:
        print 'remove file failed [Exception]', e
        return False

if __name__ == "__main__":

    debug_files = db_operation.query_ImageMagick_compile_files()
    print len(debug_files)
    processed = db_operation.query_ImageMagick_processed_compile_files()
    print processed
    #exit(0)

    i = 0
    for id, unstripped_local_url, bin_filename, tag in debug_files:
        #print id, bin_filename

        if id in processed:
            continue
        #if int(id) != 48119:
        #    continue

        if not bin_filename.endswith('.o'):
            continue

        path = unstripped_local_url
        if not udload.download_from_ceph(unstripped_local_url, path):
            print 'download failed [', unstripped_local_url, '], continue' 
            continue

        records = process_with_nm(path)
        if records == []:
            continue
        
        #print records
        save_to_db(records, id)
        clean(path)

'''
 if i > 10:
          break
        print '[', i, '/', len(debug_files), ']', id, bin_filename
        i = i + 1
'''

