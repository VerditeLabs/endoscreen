import csv
import json
import os

#todo: rewrite trie
class TrieNode:
    def __init__(self, c):
        self.char = c
        self.end = False
        self.children = {}

class Trie:
    def __init__(self):
        self.root = TrieNode("")

    def insert(self, word):
        node = self.root

        for c in word:
            if c in node.children:
                node = node.children[c]
            else:
                new_node = TrieNode(c)
                node.children[c] = new_node
                node = new_node
        node.end = True

    def dfs(self, node, prefix):
        if node.end:
            self.output.append(prefix + node.char)

        for child in node.children.values():
            self.dfs(child, prefix + node.char)

    def query(self, x):
        self.output = []
        node = self.root

        # Check if the prefix is in the trie
        for char in x:
            if char in node.children:
                node = node.children[char]
            else:
                return []

        self.dfs(node, x[:-1])
        return sorted(self.output)

def gendb(masterpath):
    db = dict()

    with open(masterpath, 'r') as f:
        reader = csv.DictReader(f)
        for line in reader:
            pmid = 'pmid:' + line['PMID'].strip()
            cid = 'cid:' + line['CID/CAS'].strip()
            chem = 'chem:' + line['Chemical'].strip().lower()
            outcomes = ['outcome:' + x.strip().lower() for x in line['Outcomes'].split(',')]

            entry = db.get(pmid, {'pmid': pmid, 'related': set()})
            entry['related'].update({cid, chem, *outcomes})
            db[pmid] = entry

            entry = db.get(cid, {'cid': cid, 'name': chem, 'related': set()})
            entry['related'].update({pmid, *outcomes})
            db[cid] = entry

            entry = db.get(chem, {'name': chem, 'cid':cid, 'related': set()})
            entry['related'].update({pmid, cid, *outcomes})
            db[chem] = entry

            for outcome in outcomes:
                entry = db.get(outcome, {'outcome': outcome, 'related': set()})
                entry['related'].update({pmid, cid, chem})
                db[outcome] = entry

    return db

def genindex(db):
    all_ids = set()
    for k, v in db.items():
        all_ids.update({k, *v['related']})

    index = Trie()

    for id in all_ids:
        index.insert(id)
    return index

class EDCDB():
    def __init__(self, dbpath):
        if not os.path.exists(dbpath):
            raise FileNotFoundError('Endoscreen_database.csv not found')

        self.db = gendb(dbpath)
        self.index = genindex(self.db)

    def api(self, ver: str, func: str, query: str):
        if ver != 'v1':
            return dict()
        if func == 'fetch':
            for k, v in self.db.items():
                if k == query:
                    return v
            else:
                return dict()
        elif func == 'search':
            return self.index.query(query)

if __name__ == '__main__':
    edcdb = EDCDB('../Endoscreen_database.csv')
    print(edcdb.api('v1', 'fetch', 'pmid:32073305'))
    print(edcdb.api('v1', 'fetch', 'cid:241'))
    print(edcdb.api('v1', 'fetch', 'pmid:1'))
    print(edcdb.api('v1', 'fetch', 'outcome:reproductive'))

    print(edcdb.api('v1', 'search', 'chem:Benzene'))
    print(edcdb.api('v1', 'search', 'benz'))
    print(edcdb.api('v1', 'search', 'bis'))
    print(edcdb.api('v1', 'search', 'r'))
    print(edcdb.api('v1', 'search', 're'))
    print(edcdb.api('v1', 'search', 'rep'))
    print(edcdb.api('v1', 'search', 'repr'))
    print(edcdb.api('v1', 'search', 'repro'))
    print(edcdb.api('v1', 'search', 'reprod'))
    print(edcdb.api('v1', 'search', 'reprodu'))
    print(edcdb.api('v1', 'search', 'reproduct'))
    print(edcdb.api('v1', 'search', 'reproducti'))
    print(edcdb.api('v1', 'search', 'reproductiv'))
    print(edcdb.api('v1', 'search', 'reproductive'))
    print(edcdb.api('v1', 'search', 'metabolic'))
