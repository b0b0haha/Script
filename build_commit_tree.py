import os
import sys
sys.path.append(os.path.abspath('../utils'))

import networkx as nx
from networkx.drawing.nx_pydot import write_dot
import pydot
import db_operation
import operator

ffmpeg = 1614410

def parse_tags(tags):
    tag_commit = {}
    tag_number = {}
    for name, commit in tags:
        if name.startswith('v') or name.startswith('n'):
            if name.endswith('-dev') or '-rc' in name:
                continue
            tag_commit[name] = commit
            elems = [int(x) for x in name[1:].split('.')]
            if len(elems) == 2:
                number = elems[0] * 10000 + elems[1] * 100
            elif len(elems) == 3:
                number = elems[0]* 10000 + elems[1] * 100 + elems[2] * 1
            else:
                continue
            tag_number[name] = number

    tag_number = sorted(tag_number.items(), key = operator.itemgetter(1))
    #print tag_number

    return tag_number, tag_commit        

def build_parentship_between_versions(high_commit, tag_number, tag_commit, k):
    try:
        g = nx.DiGraph()
        parents = db_operation.query_commit_parents(high_commit)
        print parents
        for p in parents:
            g.add_edge(high_commit, p)
        
        low_version = None
        low_commit = None
        last_parent = high_commit
        while True:
            if len(parents) == 0:
                print 'null'
                low_commit = last_parent[0]
                low_version = high_version
                break
            low_version = None
            low_commit = None
            for i in range(0, k):
                version = tag_number[k-i-1][0]
                commit = tag_commit[version]
                if commit in parents:
                    low_version = version
                    low_commit = commit
                    break
            if low_version is not None:
                break
            
            parents_l2 = []
            for p in parents:
                grandparents = db_operation.query_commit_parents(p)
                for gp in grandparents:
                    parents_l2.append(gp)
                    g.add_edge(p, gp)
            
            last_parent = parents
            parents = []
            parents = parents_l2
            print parents

        if low_version is not None:
            all_paths = nx.all_simple_paths(g, high_commit, low_commit)
            slice_g = nx.DiGraph()
            for path in all_paths:
                #print path
                for i in range(i, len(path)-1):
                    slice_g.add_edge(path[i], path[i+1])
            return slice_g, low_version

        return g, low_version
    except Exception, e:
        print e
        return None, None

def record_map(g, version, repo):
    try:
        if g is None:
            return False

        for node in g.nodes():
            if not db_operation.add_commit_tag(repo, node, version):
                print 'save failed', node
            
        return True 
    except Exception, e:
        print e
        return False

if __name__ == "__main__":
    tags = db_operation.query_tags(ffmpeg)
    #print tags
    tag_number, tag_commit = parse_tags(tags)

    for i in range(1, len(tag_number)):
        high_version = tag_number[i][0]
        high_commit = tag_commit[high_version]
        print high_version, high_commit

        #if high_version != 'n0.8':
        #    continue
        #if high_version == 'n0.7.1' or high_version == 'n4.0.1':
        #    continue

        if len(high_version.split('.')) != 2:
            continue

        if high_version == 'v0.6':
            continue

        g, low_version = build_parentship_between_versions(high_commit, tag_number, tag_commit, i)
        if low_version is None:
            continue
        record_map(g, high_version, ffmpeg)
        print low_version, len(g.nodes())
        #write_dot(g, high_version+'-'+low_version+'.dot')
        #(pg,) = pydot.graph_from_dot_file(high_version+'-'+low_version+'.dot')
        #pg.write_png(high_version+'-'+low_version+'.png')
        #break
        
