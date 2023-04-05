import csv
import json
import os
import time

import easy_entrez
from rapidfuzz import fuzz, process
from google.cloud import vision

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')

entrez_api = easy_entrez.EntrezAPI('endoscreen', 'contact@endoscreen.org', return_type='json')


if key := os.environ.get('GOOGLE_API_KEY'):
    client = vision.ImageAnnotatorClient(client_options={'api_key': key, 'quota_project_id': 'endoscreen'})
else:
    client = vision.ImageAnnotatorClient()

def filter_for_ocr(text):
    text = text.lower()
    text = ''.join(filter(str.isalnum, text))
    text = ''.join(filter(str.isascii, text))
    return text


def cas_to_cid(cas):
    try:
        time.sleep(.1)
        chem = entrez_api.search(cas.lower().replace('cas:', ''), max_results=10, database='pccompound')
        cid = chem.data['esearchresult']['idlist']
        return ['cid:' + _ for _ in cid]
    except:
        print("failed during", cas)

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



class EDCDB():
    def __init__(self):
        self.db = dict()
        for p in [
                #'data/processed/deduct_s1.csv',
                  'data/processed/deduct_s2.csv',
                  'data/processed/deduct_s3.csv',
                  'data/processed/deduct_s4.csv',
                  'data/processed/eu.csv',
                  'data/processed/tedx.csv',
                  'data/raw/Endoscreen_database.csv',
                  'data/raw/edcdb_master.csv',
                  'data/raw/DEDuCT_ENH_edited.csv'
        ]:
            with open(os.path.join(ROOTDIR, p), 'r') as f:
                reader = csv.DictReader(f)
                for line in reader:

                    pmid = 'pmid:' + pmid if (pmid:=line.get('pmid', '').strip().lower().replace('pmid:', '')) else ''
                    cid  = 'cid:'  + cid  if (cid :=line.get('cid',  '').strip().lower().replace('cid:',  '')) else ''
                    cas  = 'cas:'  + cas  if (cas :=line.get('cas',  '').strip().lower().replace('cas:',  '')) else ''
                    chem = 'chem:' + chem if (chem:=line.get('chem', '').strip().lower()) else ''

                    outcomes = {x.strip().lower() for x in outs.split(';')} if (outs:=line.get('outcomes', '')) else set()
                    synonyms = {x.strip().lower() for x in outs.split(';')} if (outs:=line.get('synonyms', '')) else set()

                    if pmid:
                        entry = self.db.get(pmid, {'pmid': pmid, 'related': {cid, cas, chem, *outcomes, *synonyms}})
                        entry['related'].update({cid, cas, chem, *outcomes, *synonyms})
                        self.db[pmid] = entry #todo: necessary?
                    if cas and not cid:
                        entry = self.db.get(cid, {'cas': cas, 'name': chem, 'synonyms': synonyms, 'related': {pmid, *outcomes}})
                        entry['related'].update({pmid, *outcomes})
                        self.db[cid] = entry
                    if cid:
                        entry = self.db.get(cid, {'cid': cid, 'name': chem, 'synonyms': synonyms, 'related': {pmid, *outcomes}})
                        entry['related'].update({pmid, cas, *outcomes})
                        self.db[cid] = entry

        for k,v in self.db.items():
            self.db[k]['related'] = sorted(v['related'])
            try:
                self.db[k]['related'].remove('')
            except:
                pass
            if 'synonyms' in v:
                self.db[k]['synonyms'] = sorted(v['synonyms'])

        self.gensyn(os.path.join(ROOTDIR, 'data', 'edcdb.json'))
        self.index = self.genindex(self.db)

        print("total db entries", len(self.db))
        print("num pmids", len({k for k in self.db.keys() if k.startswith('pmid:')}))
        print("num cids", len({k for k in self.db.keys() if k.startswith('cid:')}))

    def gensyn(self, synpath):
        with open(synpath, 'r') as f:
            papers, chems = json.load(f)
        for chem in chems:
            k = 'cid:' + chem['cid']
            if k in self.db:
                self.db[k]['synonyms'] = chem['synonyms']
                for syn in chem['synonyms']:
                    if len(syn) < 5:
                        print("short synonym",syn,chem['cid'],chem['name'])
                        continue
                    if syn in self.db:
                        self.db[syn]['syn'].append(k)
                        self.db[filter_for_ocr(syn)]['syn'].append(k)
                    else:
                        self.db[syn] = {'syn': ['cid:' + chem['cid']]}
                        self.db[filter_for_ocr(syn)] = {'syn': ['cid:' + chem['cid']]}
            else:
                pass
                #cid not in final endoscreen_database.csv
                #so skip it
                #print('skipping',k)

    def genindex(self, db):
        all_ids = set()
        for k, v in db.items():
            all_ids.update({k, *v.get('related',set()), *v.get('synonyms', set())})

        index = Trie()

        for id in all_ids:
            index.insert(id)
        return index

    def identify(self, image_data):
        print("identify")
        if not image_data:
            return []
        image = vision.Image(content=image_data)
        response = client.text_detection(image=image)

        #text_annotations[0] is always the full text that was detected
        text = filter_for_ocr(response.text_annotations[0].description)
        if 'ingredient' not in text:
            # ??? labels should _always_ contain 'ingredient', so if it's not there then
            # we probably didn't get a good photo or this isn't an ingredient list
            return [""]

        res = process.extract(text, self.db.keys(), scorer=fuzz.partial_token_sort_ratio, limit=100)
        cids = list()
        for r in res:
            if r[1] > 95 and (cid:=self.db.get(r[0])['syn'][0]) not in cids:
                cids.append(cid)
        return cids

    def api(self, ver: str, func: str, query: str):
        if ver != 'v1':
            return dict()
        if func == 'fetch':
            return [self.db.get(query, dict())]
        elif func == 'search':
            return self.index.query(query)[:500]

if __name__ == '__main__':
    edcdb = EDCDB()
    with open(os.path.join(ROOTDIR,'data','img','IMG_20230302_204644_01.jpg'),'rb') as f:
        data = f.read()
    res = edcdb.identify(data)
    print(edcdb.api('v1', 'fetch', 'pmid:32073305'))
    print(edcdb.api('v1', 'fetch', 'cid:241'))
    print(edcdb.api('v1', 'fetch', 'cid:3117'))
    print(edcdb.api('v1', 'fetch', 'pmid:1'))
    print(edcdb.api('v1', 'fetch', 'outcome:reproductive'))

    print(len(edcdb.api('v1', 'search', 'cid:')))
    print(edcdb.api('v1', 'search', 'benz'))
    print(edcdb.api('v1', 'search', 'benzene'))
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
