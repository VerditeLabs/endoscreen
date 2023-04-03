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

def gendb(masterpath, olddbpath):
    with open(olddbpath,'r') as f:
        papers, chems = json.load(f)
    conflicts = 0
    syn_to_cid = dict()
    for chem in chems:
        syns = [chem['name'], *chem['synonyms']]
        for syn in syns:
            if not syn:
                #???
                continue
            syn = syn.lower()
            if syn in syn_to_cid and syn_to_cid[syn] != chem['cid']:
                #synonym points to multiple cids?
                print('darn')
                conflicts+=1
                continue
            syn_to_cid[syn] = chem['cid']

    db = dict()
    db['paper'] = list()
    db['chem'] = list()
    db['outcome'] = list()
    db['compound'] = list()
    db['keyword'] = list()
    db['category'] = list()

    with open(masterpath, 'r') as f:
        reader = csv.DictReader(f)
        for line in reader:
            if line['Abstract'][0] in ['[', '{']:
                # probably bad json
                pass
            pmid = line['PMID'].strip()
            abstract = line['Abstract'].strip()  # todo: remove bad json
            title = line['Title']
            chems = [x.strip().lower() for x in line['Chemical'].split(',')]
            outcomes = [x.strip().lower() for x in line['Outcomes'].split(',')]
            compounds = [x.strip().lower() for x in line['Compounds'].split(',')]
            keywords = [x.strip().lower() for x in line['Keywords'].split(',')]
            categories = [x.strip().lower() for x in line['Categories'].split(',')]

            related = [*outcomes, *compounds, *keywords, *categories]

            db['paper'].append({'pmid': pmid, 'abstract': abstract, 'title': title, 'related': related + chems})

            for chem in chems:
                if not (cid := syn_to_cid.get(chem)):
                    #malformatted chemical name or something...
                    cid = '0'
                    #print()
                for i, c in enumerate(db['chem']):
                    if c['cid'] == cid:
                        db['chem'][i]['related'].update({pmid, *chems})
                        break
                else:
                    db['chem'].append({'cid': cid, 'name': chem, 'related': {*related, pmid}})

            for outcome in outcomes:
                for i, o in enumerate(db['outcome']):
                    if o['outcome'] == outcome:
                        db['outcome'][i]['related'].update({pmid, *chems})
                        break
                else:
                    db['outcome'].append({'outcome': outcome, 'related': {pmid, *chems}})

            for compound in compounds:
                for i, o in enumerate(db['compound']):
                    if o['compound'] == compound:
                        db['compound'][i]['related'].update({pmid, *chems})
                        break
                else:
                    db['compound'].append({'compound': compound, 'related': {pmid, *chems}})

            for keyword in keywords:
                for i, o in enumerate(db['keyword']):
                    if o['keyword'] == keyword:
                        db['keyword'][i]['related'].update({pmid, *chems})
                        break
                else:
                    db['keyword'].append({'keyword': keyword, 'related': {pmid, *chems}})

            for category in categories:
                for i, o in enumerate(db['category']):
                    if o['category'] == category:
                        db['category'][i]['related'].update({pmid, *chems})
                        break
                else:
                    db['category'].append({'category': category, 'related': {pmid, *chems}})


    #preprocess the db by doing some sorting
    db['paper'] = sorted(db['paper'], key=lambda x: int(x['pmid']))
    db['chem'] = sorted(db['chem'], key=lambda x: int(x['cid']))

    with open('edcdb_master.json', 'w+') as f:
        class SetEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, set):
                    return list(obj)
                return json.JSONEncoder.default(self, obj)

        json.dump(db, f, cls=SetEncoder)
    return db

def genindex(db):
    all_ids = set()
    for paper in db['paper']:
        all_ids.update({paper['pmid'], *paper['related']}) #todo: add title?
    for chem in db['chem']:
        all_ids.update({chem['cid'], chem['name'], *chem['related']})
    for outcome in db['outcome']:
        all_ids.update({outcome['outcome'], *outcome['related']})
    for compound in db['compound']:
        all_ids.update({compound['compound'], *compound['related']})
    for keyword in db['keyword']:
        all_ids.update({keyword['keyword'], *keyword['related']})
    for category in db['category']:
        all_ids.update({category['category'], *category['related']})
    index = Trie()

    for id in all_ids:
        if id == '':
            continue
        index.insert(id)
    return index

class EDCDB():
    def __init__(self, path, olddbpath):
        if os.path.exists('../Endoscreen_database.csv'):
            self.db = gendb('../Endoscreen_database.csv', olddbpath)
        else:
            self.db = gendb(path, olddbpath)
        self.index = genindex(self.db)


    def api(self, ver: str, func: str, query: str):
        if ver != 'v1':
            return dict()
        if func == 'fetch':
            tag, term = query.split(':')
            field = {'pmid': 'paper', 'cid': 'chem'}.get(tag, tag)

            #todo: make better
            for e in self.db[field]:
                if e[tag] == term:
                    return e
            else:
                return dict()
        elif func == 'search':
            return self.index.query(query)

def import_csv(path):
    import csv
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

if __name__ == '__main__':
    edcdb = EDCDB('../edcdb_master.csv','../termsdb.json')
    print(edcdb.api('v1', 'fetch', 'pmid:32073305'))
    print(edcdb.api('v1', 'fetch', 'cid:241'))
    print(edcdb.api('v1', 'fetch', 'pmid:1'))
    print(edcdb.api('v1', 'fetch', 'keyword:flame retardants'))
    print(edcdb.api('v1', 'fetch', 'outcome:reproductive'))
    print(edcdb.api('v1', 'fetch', 'category:bone density'))
    print(edcdb.api('v1', 'fetch', 'compound:phthalic acid'))

    print(edcdb.api('v1', 'search', 'benzene'))
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
