import gzip
import json
import os
import csv
from collections import defaultdict
import cProfile

import pandas as pd
import numpy as np

ELSEVIER_API_KEY = os.environ.get('ELSEVIER_API_KEY')



def gen_newtfidf(corpus):

    tfidf = TfidfVectorizer()
    preprocess = tfidf.build_preprocessor()

    chunksz = 1000
    scores = dict()
    num_docs = 0
    texts = []
    i = 0

    for line in corpus:
        if num_docs == 1000001:
            break
        num_docs += 1
        i+=1
        pp = preprocess(line)
        texts.append(pp)
        #print(i)
        if i == chunksz:
            print('processing chunk',num_docs)
            result = tfidf.fit_transform(texts)
            for ele1, ele2 in sorted(zip(tfidf.get_feature_names(), tfidf.idf_), key=lambda x: x[1]):
                print(ele1,ele2)
                if ele1 in scores:
                    scores[ele1] = scores[ele1] + ele2
                else:
                    scores[ele1] = ele2
            #print()
            texts = []
            i = 0
    #for k,v in sorted(scores.items(),key=lambda x:x[1]):
    #    print(k,v)




    print()




def tfidf(corpus):
    all_words = set()



def get_pubmed_data(article):
    title = article['MedlineCitation']['Article']['ArticleTitle']
    if isinstance(title, dict):
        try:
            title = title['#text']
        except:
            title = 'Im too stupid to title my paper correctly'
    if title is None:
        title = 'Im too stupid to title my paper'
    pmid = article['MedlineCitation']['PMID']['#text']
    journal = article['MedlineCitation']['Article']['Journal']['Title']
    if not isinstance(journal, str):
        # print()
        pass
    try:
        abstract = article['MedlineCitation']['Article']['Abstract']['AbstractText']
    except:
        abstract = ''
    if isinstance(abstract, list):
        try:
            abstract = [thing['#text'] for thing in abstract]
        except:
            # if your paper gets then you suck
            abstract = ''
        abstract = ','.join(abstract)
    elif isinstance(abstract, dict):
        try:
            abstract = abstract['#text']
        except:
            abstract = 'I suck at formatting my pubmed entries'
    if abstract is None:
        abstract = '?????????????'

    try:
        chemicals = article['MedlineCitation']['ChemicalList']['Chemical']
    except:
        chemicals = []
    if not isinstance(chemicals, list):
        chemicals = [chemicals]
    if len(chemicals) > 0 and isinstance(chemicals[0], dict):
        chemicals = [thing['NameOfSubstance']['#text'] for thing in chemicals]

    try:
        date = article['MedlineCitation']['DateCompleted']
    except:
        date = article['MedlineCitation']['DateRevised']
    date = date['Day'] + '-' + date['Month'] + '-' + date['Year']

    try:
        topics = article['MedlineCitation']['MeshHeadingList']['MeshHeading']
    except:
        topics = []
    if not isinstance(topics, list):
        topics = [topics]
    try:
        topics = [thing['#text'] for thing in topics]
    except:
        topics = [thing['DescriptorName']['#text'] for thing in topics]

    try:
        keywords = article['MedlineCitation']['KeywordList']['Keyword']
    except:
        keywords = []
    if not isinstance(keywords, list):
        keywords = [keywords]
    try:
        keywords = [thing['#text'] for thing in keywords]
    except:
        keywords = []

    try:
        pubtype = article['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']
        if not isinstance(pubtype, list):
            pubtype = [pubtype]
        pubtype = [thing['#text'] for thing in pubtype]
    except:
        pubtype = []

    pubtype = ','.join(pubtype)
    keywords = ','.join(keywords)
    chemicals = ','.join(chemicals)
    topics = ','.join(topics)

    return pmid, title, journal, date, pubtype, abstract, chemicals, topics, keywords

def offline_csv_search():
    indir = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/baseline'
    for file in reversed(sorted(os.listdir(indir))):
        infilepath = os.path.join(indir, file)
        if not file.endswith('.csv'):
            continue
        with open(infilepath, 'r') as f:
            for line in f:
                yield line

def offline_json_search():
    indir = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/asjson'
    for file in reversed(sorted(os.listdir(indir))):
        if not file.endswith('.json.gz'):
            continue
        print('scanning', file)
        with gzip.open(os.path.join(indir, file), 'rb') as in_f:
            parsed = json.loads(in_f.read())

        for article in parsed['PubmedArticleSet']['PubmedArticle']:
            yield get_pubmed_data(article)



from sklearn.feature_extraction.text import TfidfVectorizer

def gen_tfidf():
    badtexts = []
    corpus = defaultdict(lambda:0)

    goodtfidf = TfidfVectorizer()
    pp = goodtfidf.build_preprocessor()
    tk = goodtfidf.build_tokenizer()
    for i, paper in enumerate(offline_csv_search()):
        #pmid, title, journal, date, pubtype, abstract, chemicals, topics, keywords = paper
        pmid, title, journal, date, pubtype, abstract, chemicals, topics, keywords = \
            paper['pmid'], paper['title'], paper['journal'], paper['date'], paper['pubtype'], paper['abstract'], paper['chemicals'], paper['meshterms'], paper['keywords']
        searchable = ' '.join([title, abstract, chemicals, topics, keywords])
        searchable = pp(searchable)
        searchable = searchable.replace('-','')
        tkns = tk(searchable)
        for tkn in tkns:
            corpus[tkn]+=1
        badtexts.append(searchable)
        if i % 10000 == 0:
            print(i)
        if i >= 2000000:
            break

    with open('../termsdb.json','r') as f:
        papers, chems = json.load(f)
    goodtexts = list()
    for p in papers:
        #print(p)
        searchable = ' '.join([p['title'], p['abstract'],*p['related']])
        goodtexts.append(searchable)
        #goodtexts.append()
    print("generating tfidf for good papers")
    goodresult = goodtfidf.fit_transform(goodtexts)
    gooddict = dict()

    for ele1, ele2 in sorted(zip(goodtfidf.get_feature_names(), goodtfidf.idf_),key=lambda x:x[1]):
        gooddict[ele1] = ele2

    badtfidf = TfidfVectorizer()

    print("generating tfidf for bad papers")
    badresult = badtfidf.fit_transform(badtexts)
    baddict = dict()

    for ele1, ele2 in sorted(zip(badtfidf.get_feature_names(), badtfidf.idf_), key=lambda x: x[1]):
        baddict[ele1] = ele2


with open('../termsdb.json','r') as f:
    papers, chems = json.load(f)
goodtexts = list()
for p in papers:
    #print(p)
    searchable = ' '.join([p['title'], p['abstract'],*p['related']])
    goodtexts.append(searchable)
    #goodtexts.append()
gen_newtfidf(goodtexts)