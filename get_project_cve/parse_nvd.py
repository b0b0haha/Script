import os
import pymongo 
import json
from termcolor import colored


def parse_json(nvd_json, db):
    try:
        data = None 
        with open(nvd_json, 'r') as fd:
            data = json.load(fd)
        for item in data['CVE_Items']:
            cve_id = item['cve']['CVE_data_meta']['ID']
            print colored(cve_id+':', 'green')

            cve = db.item_str.find_one({'id':cve_id})
            if cve is None:
                print colored('not found cve item\n', 'red')
                continue
            if 'nvd' in cve.keys() and cve['nvd'] is not None:
                print colored('This item has been appended\n', 'red')
                continue
            db.item_str.update_one({'id':cve_id}, {'$set': {'nvd': item}})
            print colored('[ok]\n', 'green')
            #break
    except Exception as e:
        print(e)
        return None

def parse_multi_json(folder, db):
    try:
        for root, _, files in os.walk(folder):
            for fname in files:
                if not fname.endswith('.json'):
                    continue
                fpath = os.path.join(root, fname)
                print colored(fpath, 'blue')
                parse_json(fpath, db)
                #break
    except Exception as e:
        print(e)
        return None

def main():
    client = pymongo.MongoClient('172.18.108.169', 21087)
    db = client.cve_nvd
    data_folder = './cve_nvd'
    parse_multi_json(data_folder, db)


def add_info_to_cve_meta():
    try:
        client = pymongo.MongoClient('172.18.108.219', 27087)
        db = client.imagemagick
        cve_metas = db.cve_commit_meta_1107.find({})
        for cve_meta in cve_metas:
            if 'cve' not in cve_meta or cve_meta['cve'] is None:
                continue
            print colored(cve_meta['cve'], 'green')
            item = client.cve.item_str.find_one({'_id':cve_meta['cve']})
            if item is None or 'nvd' not in item:
                continue
            cwe = []
            for pd in item['nvd']['cve']['problemtype']['problemtype_data']:
                for desc in pd['description']:
                    cwe.append(desc['value'])
            print colored(str(cwe), 'blue')
            impact = {}
            impact['baseMetricV2'] = {'cvssV2_baseScore': item['nvd']['impact']['baseMetricV2']['cvssV2']['baseScore'],
                                      'cvssV2_severity': item['nvd']['impact']['baseMetricV2']['severity']}
            if 'baseMetricV3' in item['nvd']['impact']:
                impact['baseMetricV3'] = {'cvssV3_baseScore': item['nvd']['impact']['baseMetricV3']['cvssV3']['baseScore'],
                                          'cvssV3_severity': item['nvd']['impact']['baseMetricV3']['cvssV3']['baseSeverity']}
            print colored(str(impact), 'blue')
            db.cve_commit_meta_1107.update_one({'cve': cve_meta['cve']}, {'$set': {'cwe': cwe, 'impact': impact}})
            #break
    except Exception as e:
        print(e)
        return None

if __name__ == "__main__":
    # parse nvd data and save into 'cve.item_str' collection
    main()

    # add cwe and impact info into 'cve_commit_meta_1107' collection
    #add_info_to_cve_meta()
