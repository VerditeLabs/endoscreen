import csv
import gzip
import time
import os
import json

from collections import defaultdict
import easy_entrez
import xmltodict
import pubchempy as pcp

from easy_entrez.parsing import xml_to_string


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

    # pmid = pmid.decode('ascii', 'ignore')
    # title = title.decode('ascii', 'ignore')
    # journal = journal.decode('ascii', 'ignore')
    # date = date.decode('ascii', 'ignore')
    # pubtype = pubtype.decode('ascii', 'ignore')
    # abstract = abstract.decode('ascii', 'ignore')
    # chemicals = chemicals.decode('ascii', 'ignore')
    # topics = topics.decode('ascii', 'ignore')
    # keywords = keywords.encode('ascii', 'ignore')

    return pmid, title, journal, date, pubtype, abstract, chemicals, topics, keywords


def get_offline_articles_from_csv():
    indir = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/baseline'
    for file in reversed(sorted(os.listdir(indir))):
        infilepath = os.path.join(indir, file)
        if not file.endswith('.csv'):
            continue
        with open(infilepath, 'r') as f:
            reader = csv.DictReader(f)
            for line in reader:
                yield line


def get_offline_articles():
    indir = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/asjson'
    for file in reversed(sorted(os.listdir(indir))):
        infilepath = os.path.join(indir, file)
        if not infilepath.endswith('.json.gz'):
            continue
        with gzip.open(infilepath, 'r') as in_f:
            parsed = json.load(in_f)
            for article in parsed['PubmedArticleSet']['PubmedArticle']:
                yield article


def search_offline_csvs():
    path = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/baseline'
    with open('offline_pubmed_searched.csv', 'w') as out_f:
        writer = csv.DictWriter(out_f,
                                ['pmid', 'title', 'journal', 'date', 'pubtype', 'abstract', 'chemicals', 'meshterms',
                                 'keywords'])
        writer.writeheader()
        num = 0
        for file in reversed(sorted(os.listdir(path))):
            if not file.endswith('.csv'):
                continue
            with open(os.path.join(path, file), 'r') as in_f:
                reader = csv.DictReader(in_f)

                for line in reader:
                    pmid = line['pmid']
                    title = line['title']
                    journal = line['journal']
                    date = line['date']
                    pubtype = line['pubtype']
                    abstract = line['abstract']
                    chemicals = line['chemicals']
                    meshterms = line['meshterms']
                    keywords = line['keywords']

                    searchable = title + abstract + chemicals + keywords + meshterms
                    if 'endocrine' in searchable and 'disrupt' in searchable:
                        for thing in exclusion_list:
                            if thing in searchable:
                                break
                        else:
                            print(pmid)
                            num += 1
                            print(num)
                            writer.writerow(line)


def convert_pubmed_to_json():
    indir = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/baseline'
    outdir = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/asjson'
    for file in reversed(sorted(os.listdir(indir))):
        infilepath = os.path.join(indir, file)
        outfilepath = os.path.join(outdir, file).replace('.xml.gz', '.json.gz')
        if not file.endswith('.xml.gz'):
            continue
        if os.path.exists(outfilepath):
            continue
        print("converting", infilepath, 'to json', outfilepath)
        with gzip.open(infilepath, 'r') as in_f, gzip.open(outfilepath, 'w') as out_f:
            json.dump(xmltodict.parse(in_f), out_f)


def offline_json_search():
    indir = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/asjson'
    for file in reversed(sorted(os.listdir(indir))):
        infilepath = os.path.join(indir, file)
        if not infilepath.endswith('.json.gz'):
            continue
        print('scanning', file)
        with gzip.open(infilepath, 'rb') as in_f:
            parsed = json.loads(in_f.read())
            for article in parsed['PubmedArticleSet']['PubmedArticle']:

                pmid, title, journal, date, pubtype, abstract, chemicals, topics, keywords = get_pubmed_data(article)

                cited_pmids = set()
                if 'ReferenceList' in article['PubmedData']:
                    if 'Reference' in article['PubmedData']['ReferenceList']:
                        refs = article['PubmedData']['ReferenceList']['Reference']
                        if not isinstance(refs, list):
                            refs = [refs]
                        for ref in refs:
                            if 'ArticleIdList' in ref:
                                if 'ArticleId' in ref['ArticleIdList']:
                                    ids = ref['ArticleIdList']['ArticleId']
                                    if not isinstance(ids, list):
                                        ids = [ids]
                                    for id in ids:
                                        if id['@IdType'] == 'pubmed':
                                            cited_pmids.add(id['#text'])

                searchable = title + abstract + chemicals + keywords + topics
                searchable = searchable.decode('ascii')
                for thing in exclusion_list:
                    if thing in searchable:
                        break
                else:
                    if 'endocrine' in searchable and 'disrupt' in searchable:
                        print(pmid)
                        print(cited_pmids)


def offline_search():
    path = '/Users/forrest/pubmed/ftp.ncbi.nlm.nih.gov/pubmed/baseline'
    print(sorted(os.listdir(path)))
    for file in reversed(sorted(os.listdir(path))):
        inpath = os.path.join(path, file)
        outpath = inpath.replace('.xml.gz', '.csv')
        if not file.endswith('.xml.gz'):
            continue
        if os.path.exists(outpath):
            continue
        with gzip.open(inpath, 'r') as in_f, open(outpath, 'w') as out_f:
            out = []
            print("parsing", file)
            parsed = xmltodict.parse(in_f)

            for article in parsed['PubmedArticleSet']['PubmedArticle']:
                title = article['MedlineCitation']['Article']['ArticleTitle']
                journal = article['MedlineCitation']['Article']['Journal']['Title']
                try:
                    abstract = article['MedlineCitation']['Article']['Abstract']['AbstractText']
                    if not isinstance(abstract, str):
                        print()
                    if abstract is None:
                        abstract = ''
                except:
                    abstract = ''

                try:
                    chemicals = article['MedlineCitation']['ChemicalList']['Chemical']
                    if isinstance(chemicals, dict):
                        chemicals = [chemicals]
                    chemicals = ','.join(chem['NameOfSubstance']['#text'].strip() for chem in chemicals)
                except:
                    chemicals = ''
                pmid = article['MedlineCitation']['PMID']['#text']
                try:
                    date = article['MedlineCitation']['DateCompleted']
                except:
                    try:
                        date = article['MedlineCitation']['DateRevised']
                    except:
                        pass
                date = date['Day'] + '-' + date['Month'] + '-' + date['Year']
                try:
                    topics = article['MedlineCitation']['MeshHeadingList']['MeshHeading']
                    if isinstance(topics, dict):
                        topics = [topics]
                    topics = ','.join(topic['DescriptorName']['#text'].strip() for topic in topics)
                except:
                    topics = ''
                try:
                    keywords = article['MedlineCitation']['KeywordList']['Keyword']
                    keywords = ','.join(word['#text'].strip() for word in keywords)
                except:
                    keywords = ''
                try:
                    publication_type = article['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']
                    if isinstance(publication_type, dict):
                        publication_type = [publication_type]
                    pubtype = ','.join([t['#text'] for t in publication_type])
                except:
                    pubtype = ''
                # print(chemicals,topics,keywords)
                pmid = pmid.encode('ascii', 'ignore')
                try:
                    title = title.encode('ascii', 'ignore')
                except:
                    title = ''
                journal = journal.encode('ascii', 'ignore')
                date = date.encode('ascii', 'ignore')
                pubtype = pubtype.encode('ascii', 'ignore')
                try:
                    # todo: looks like some abstracts eist
                    abstract = abstract.encode('ascii', 'ignore')
                except:
                    abstract = ''
                chemicals = chemicals.encode('ascii', 'ignore')
                topics = topics.encode('ascii', 'ignore')
                keywords = keywords.encode('ascii', 'ignore')
                out.append({'pmid': pmid, 'title': title, 'journal': journal, 'date': date, 'pubtype': pubtype,
                            'abstract': abstract, 'chemicals': chemicals, 'meshterms': topics,
                            'keywords': keywords})
                if 'endocrine' in abstract and 'disrupt' in abstract:
                    print(pmid)
            writer = csv.DictWriter(out_f, ['pmid', 'title', 'journal', 'date', 'pubtype', 'abstract', 'chemicals',
                                            'meshterms', 'keywords'])
            writer.writeheader()
            writer.writerows(out)


def cas_to_cid():
    import easy_entrez
    from raw_data import ALL_CHEMS_CAS
    from easy_entrez.parsing import xml_to_string
    all_cids = set()
    leftover_cas = set()
    entrez_api = easy_entrez.EntrezAPI(
        'endoscreen',
        'contact@endoscreen.org',
        # optional
        return_type='json'
    )
    import time
    for cas in ALL_CHEMS_CAS:
        try:
            time.sleep(.5)
            chem = entrez_api.search(cas.replace('CAS:', ''), max_results=10, database='pccompound')
            cid = chem.data['esearchresult']['idlist']
            if len(cid) == 0:
                leftover_cas.add(cas)
            else:
                all_cids.update(cid)
            print(all_cids)
        except:
            print("failed during", cas)
    print("all cids", all_cids)
    print("leftover cids", leftover_cas)


def find_lit2():
    import easy_entrez
    from easy_entrez.parsing import xml_to_string
    import xmltodict
    entrez_api = easy_entrez.EntrezAPI('endoscreen', 'verditelabs@gmail.com', return_type='json')
    search_term = ''
    res = entrez_api.search(search_term, max_results=99999, database='pubmed')
    print("found this many articles", len(res.data['esearchresult']['idlist']))
    fetched = entrez_api.fetch(res.data['esearchresult']['idlist'], max_results=1000, database='pubmed')
    parsed = xmltodict.parse(xml_to_string(fetched.data))

    print(res)


def find_literature():
    import easy_entrez
    from easy_entrez.parsing import xml_to_string
    import xmltodict
    entrez_api = easy_entrez.EntrezAPI(
        'endoscreen',
        'verditelabs@gmail.com',
        # optional
        return_type='json'
    )
    from collections import defaultdict
    out = defaultdict(list)
    fetched_out = defaultdict(list)
    with open('all_common_names.txt', 'r') as f:
        for line in f:
            name = line.strip()
            # names are crazy, let's keep to more common stuff
            if '(' in name or ',' in name:
                continue
            time.sleep(1)
            res = entrez_api.search(name + ' AND endocrine', max_results=100, database='pubmed')
            if res.data['esearchresult']['count'] == '0':
                continue
            # summary = entrez_api.summarize(res.data['esearchresult']['idlist'], max_results = 100)
            fetched = entrez_api.fetch(res.data['esearchresult']['idlist'], max_results=100, database='pubmed')
            parsed = xmltodict.parse(xml_to_string(fetched.data))
            print(name, "got", len(parsed['PubmedArticleSet']['PubmedArticle']), 'hits')
            fetched_out[name] = parsed['PubmedArticleSet']['PubmedArticle']
    import json
    with open('name_to_pmids_summary.json', 'w') as f:
        f.write(json.dumps(out))
    with open('name_to_fetched_data.json', 'w') as f:
        json.dump(fetched_out, f)


def contains_lowercase(s):
    for c in s:
        if ord('a') <= ord(c) <= ord('z'):
            return True
    return False


def get_common_names():
    import pubchempy as pcp
    all_names = set()
    with open('all_cids2.txt', 'r') as f:
        for line in f:
            line = line.strip().replace('CID:', '')
            cid = int(line)
            chem = pcp.Compound.from_cid(cid)
            print(chem.iupac_name)
            all_names.add(chem.iupac_name)
    print("all names", all_names)


def process_manual_search():
    import csv
    all_pmids = set()
    out = list()

    journals = defaultdict(lambda: 0)
    with open('manual_pubmed_search.csv', 'r') as f:
        for line in csv.DictReader(f):
            if line['PMID'] in all_pmids:
                continue
            all_pmids.add(line['PMID'])
            print(line)
            pmid, title, journal, date = line['PMID'], line['Title'], line['Journal/Book'], line['Create Date']
            journals[journal] += 1
            out.append([pmid, title, journal, date])

    print("num pmids", len(all_pmids))
    with open('manual_processed_summary.csv', 'w') as f:
        fieldnames = ['pmid', 'title', 'journal', 'date']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for line in out:
            writer.writerow({'pmid': line[0], 'title': line[1], 'journal': line[2], 'date': line[3]})
    for k, v in reversed(sorted(journals.items(), key=lambda item: item[1])):
        print(k, v)
    print("wrote rows")
    print("num journals", len(journals))


def sanitize_synonyms():
    # synonyms be crazy, let's process them some
    banned_terms = [
        '[', ']', '%', '>', '=', '<', ';', '{', '}'  # filter out weird punctuation stuff
                                                'CAS', 'CCRIS', 'CHEBI', 'CHEMBL', 'DSSTox', 'NCGC', 'NSC', 'NCI',
        # other identifiers?
        'Caswell', 'MLS', 'MFCD', 'STL', 'Tox', 'bmse', 'EINECS', 'ENT', 'ZINC',
        'UNII', 'VS-', 'WLN', 'BDBM', 'CCG', 'CS', '_',
        'British', 'European', 'antibiotic', 'KBio', 'BPBio', 'Spectrum',
        'Prestwick', 'component', 'reference', 'ampule', 'injectable',
        'reagent', 'powder', 'tested', 'mg/mL', 'FEMA', 'BSPBio', 'United States', 'mixture',
        '(VAN)', '(1:1)', '/mL', 'byproduct', 'EPA', 'Standard', '(TN)', 'german', 'indicator',
        'biological', 'Commission', 'Pesticide', 'RCRA', '(R)', 'TraceCERT', '(alpha)', '(INN)',
        '.beta.', '.alpha.', 'diameter', 'length', 'elemental', 'metallic', 'g/g', '/', 'GRADE',
        'Nanopowder', 'Dispersion', 'Powder', 'dia', 'unpurified', '#', 'ACon', 'Lopac', 'MEGxp',
        'Biomo', 'KBio', '(TBB)', 'Reference', 'Handbook', 'Epitope', 'Rcra'
    ]

    names = None
    processed_names = dict()
    with open('cid_synonym_map.json', 'r') as f:
        names = json.load(f)
    for k, v in names.items():
        keep = set()
        for synonym in v:
            asdf = [term in synonym for term in banned_terms]
            if any(term in synonym for term in banned_terms):
                continue
            if not contains_lowercase(synonym):
                continue
            keep.add(synonym)
        processed_names[k] = sorted(list(keep))
    with open('processed_synonyms.json', 'w') as f:
        json.dump(processed_names, f)


my_list = ['geeks', 'for', 'geeks', 'like',
           'geeky', 'nerdy', 'geek', 'love',
           'questions', 'words', 'life']


def chunkify(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


def parse_pubmed():
    entrez_api = easy_entrez.EntrezAPI(
        'endoscreen',
        'verditelabs@gmail.com',
        # optional
        return_type='json'
    )
    chem_occurrances = defaultdict(lambda: 0)
    mesh_occurrances = defaultdict(lambda: 0)
    keyword_occurrances = defaultdict(lambda: 0)
    out = list()
    with open('manual_processed_summary.csv', 'r') as f:
        reader = csv.DictReader(f)
        iter = 0
        for batch in chunkify(list(reader), 100):
            print("num processed", iter)
            iter += 1
            if iter > 10:
                pass
            time.sleep(.3)
            pmids = [i['pmid'] for i in batch]
            fetched = entrez_api.fetch(pmids, max_results=100, database='pubmed')
            parsed = xmltodict.parse(xml_to_string(fetched.data))
            for article in parsed['PubmedArticleSet']['PubmedArticle']:
                try:
                    citation = article['MedlineCitation']

                    title = citation['Article']['ArticleTitle']
                    journal = citation['Article']['Journal']['Title']
                    abstract = citation['Article']['Abstract']['AbstractText']
                    chemicals = citation['ChemicalList']['Chemical']
                    pmid = citation['PMID']['#text']
                    meshterms = citation['MeshHeadingList']['MeshHeading']
                    keywords = citation['KeywordList']['Keyword']
                    pubtype = citation['Article']['PublicationTypeList']['PublicationType']
                    date = citation['DateCompleted']

                    date = date['Day'] + '-' + date['Month'] + '-' + date['Year']
                    chemicals = ','.join(t['NameOfSubstance']['#text'] for t in chemicals)
                    meshterms = ','.join(t['DescriptorName']['#text'] for t in meshterms)
                    keywords = ','.join(t['#text'] for t in keywords)
                    pubtype = ','.join(t['#text'] for t in pubtype)

                    out.append({'pmid': pmid,
                                'title': title,
                                'journal': journal,
                                'date': date,
                                'pubtype': pubtype,
                                'abstract': abstract,
                                'chemicals': chemicals,
                                'meshterms': meshterms,
                                'keywords': keywords})

                except:
                    pass
    with open('out_summary.csv', 'w') as f:
        writer = csv.DictWriter(f, ['pmid', 'title', 'journal', 'date', 'pubtype', 'abstract', 'chemicals', 'meshterms',
                                    'keywords'])
        writer.writeheader()
        writer.writerows(out)

def analyze_frequency(s: str):
    import string
    from raw_data import MOST_COMMON_WORDS
    # returns a filtered word frequency for s

    # preprocess s
    s = s.lower()
    # TODO: collapse some punctuated terms, e.g. anti-estrogenic, in-vivo
    # into single words so that they aren't split into 2 words

    # remove punctuation
    s = s.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    # s = s.split()
    s = filter(lambda x: x not in MOST_COMMON_WORDS, s.split())
    s = filter(lambda x: not x.isnumeric(), s)
    s = filter(lambda x: len(x) > 1, s)
    freq = defaultdict(lambda: 0)
    for word in s:
        # print(word)
        freq[word] += 1
    return freq


def do_pubmed_freq_analysis():
    with open('badwords.txt','r') as f:
        words = f.readlines()
        WORDS = {w.strip() for w in words}

    out = list()

    num = 0
    articles = 0
    for article in get_offline_articles_from_csv():
        num += 1
        # if num > 100000:
        #    break
        # for article in get_offline_articles():
        # pmid, title, journal, date, pubtype, abstract, chemicals, topics, keywords = get_pubmed_data(article)
        # searchable = ' '.join(get_pubmed_data(article))
        pmid = article['pmid']
        if len(article['abstract']) < 100:
            continue
        searchable = ' '.join(article.values())
        searchable = searchable.lower()

        score = 0
        if ('endocrine' in searchable and 'disrupt' in searchable):
            freq = analyze_frequency(searchable)
            for k, v in freq.items():
                if k in searchable:
                    score -= v

            articles += 1
            print(articles)
            freq = list(reversed(sorted(freq.items(),key=lambda x: x[1])))
            print(pmid, score, )
            #for f in freq:
            #    if f[1] > 1:
            #        print (f)
            article['score'] = score
            out.append(article)
    with open('pubmed_freq_scores.csv', 'w') as f:
        columns = ['pmid', 'score', 'title', 'date', 'journal', 'pubtype', 'abstract', 'chemicals', 'topics',
                   'keywords', 'meshterms']
        writer = csv.DictWriter(f, columns)
        writer.writeheader()
        out = reversed(sorted(out, key=lambda x: x['score']))
        writer.writerows(out)


def gen_deduct_freq_analysis():
    from raw_data import ALL_PAPERS, MOST_COMMON_WORDS, HIGH_SCORE_TERMS, LOW_SCORE_TERMS,EXCLUDE_TERMS
    from scratch_19 import DEDUCT_FINAL_PAPERS
    entrez_api = easy_entrez.EntrezAPI(
        'endoscreen',
        'contact@endoscreen.orgm',
        # optional
        return_type='json'
    )

    ALL_PAPERS = ALL_PAPERS.difference(DEDUCT_FINAL_PAPERS)

    #fetched = entrez_api.fetch([str(p) for p in list(DEDUCT_FINAL_PAPERS)], max_results=4000, database='pubmed')
    fetched = entrez_api.fetch([str(p) for p in list(ALL_PAPERS)[:9999]], max_results=9999, database='pubmed')
    fetched2 = entrez_api.fetch([str(p) for p in list(ALL_PAPERS)[9999:]], max_results=9999, database='pubmed')

    parsed = xmltodict.parse(xml_to_string(fetched.data))
    parsed2 = xmltodict.parse(xml_to_string(fetched2.data))
    parsed['PubmedArticleSet']['PubmedArticle'].extend(parsed2['PubmedArticleSet']['PubmedArticle'])
    # print(parsed)
    out = defaultdict(lambda: 0)
    num_words = 0
    for article in parsed['PubmedArticleSet']['PubmedArticle']:
        searchable = ' '.join(get_pubmed_data(article))
        num_words += len(searchable.split())
        freq = analyze_frequency(searchable)
        # print(freq)
        for k, v in freq.items():
            out[k] += v
    with open('deduct_word_scores.json', 'w') as f:
        json.dump(out, f)
    for k,w in reversed(sorted(out.items(), key=lambda x: x[1])):
        print(k)



def listify(l):
    if isinstance(l, list):
        return l
    return [l]


def genfreq2():
    pass


def get_related(fetched, info):
    pass
    s = ''
    score = 0
    related = set()

    print(fetched['MedlineCitation']['PMID']['#text'], "score", score, related)
    # print(fetched.__repr__())
    # print(fetched.__str__())
    # related


def gen_paperinfo():
    import os
    api = easy_entrez.EntrezAPI('endoscreen', 'contact@endoscreen.org', return_type='json', api_key=os.environ['NCBI_API_KEY'])

    papers = list()

    count = 0
    for chunk in chunkify(list(DEDUCT_FINAL_PAPERS), 50):
        time.sleep(1)
        print("count", count)
        lst = [p.replace('PMID:', '') for p in chunk]
        try:
            fetched = xmltodict.parse(xml_to_string(api.fetch(lst, max_results=100).data))
            while 'PubmedArticleSet' not in fetched:
                print("trying again...")
                fetched = xmltodict.parse(xml_to_string(api.fetch(lst, max_results=100).data))
        except:
            fetched = xmltodict.parse(xml_to_string(api.fetch(lst, max_results=100).data))
            while 'PubmedArticleSet' not in fetched:
                print("trying again...")
                fetched = xmltodict.parse(xml_to_string(api.fetch(lst, max_results=100).data))

        # todo: investigate why this can fail
        # assert len(chunk) == len(fetched['PubmedArticleSet']['PubmedArticle'])
        for paper in fetched['PubmedArticleSet']['PubmedArticle']:
            info = dict()

            info['ids'] = list()
            for aid in listify(paper['PubmedData']['ArticleIdList']['ArticleId']):
                info['ids'].append(':'.join([aid['@IdType'], aid['#text']]))

            info['pubdate'] = ''
            for date in listify(paper['PubmedData']['History']['PubMedPubDate']):
                if date['@PubStatus'] == 'pubmed':
                    info['pubdate'] = '{Day}-{Month}-{Year}'.format(**date)

            info['authors'] = list()
            if 'AuthorList' in paper['MedlineCitation']['Article']:
                for author in listify(paper['MedlineCitation']['Article']['AuthorList']['Author']):
                    a = author.get('LastName')
                    if a:
                        if f := author.get('ForeName'):
                            a += ', ' + f
                    else:
                        a = author.get('CollectiveName')
                    info['authors'].append(a)
            else:
                pass

            info['title'] = paper['MedlineCitation']['Article']['ArticleTitle']
            if isinstance(info['title'], dict):
                info['title'] = info['title']['#text']
            info['pubtypes'] = list()
            for pub in listify(paper['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']):
                info['pubtypes'].append(pub['#text'])

            # todo: get citations and cited by

            info['journal'] = paper['MedlineCitation']['Article']['Journal']['Title']

            if 'Abstract' in paper['MedlineCitation']['Article']:
                info['abstract'] = paper['MedlineCitation']['Article']['Abstract']['AbstractText']
                if isinstance(info['abstract'], list):
                    abstract = ''
                    for section in info['abstract']:
                        abstract = abstract + section['@Label'] + " " + section['#text']
                    info['abstract'] = abstract
                elif isinstance(info['abstract'], dict):
                    info['abstract'] = info['abstract']['#text']
            else:
                info['abstract'] = ''

            terms = list()
            if 'ChemicalList' in paper['MedlineCitation']:
                for chem in listify(paper['MedlineCitation']['ChemicalList']['Chemical']):
                    terms.append(chem['NameOfSubstance']['#text'])
            if 'MeshHeadingList' in paper['MedlineCitation']:
                for mesh in listify(paper['MedlineCitation']['MeshHeadingList']['MeshHeading']):
                    terms.append(mesh['DescriptorName']['#text'])
            if 'KeywordList' in paper['MedlineCitation']:
                for keyword in listify(paper['MedlineCitation']['KeywordList']['Keyword']):
                    terms.append(keyword['#text'])

            terms = [s.lower() for s in terms]
            terms = [s.replace(',', '').replace('-', '') for s in terms]

            info['related'] = list(terms)

            papers.append(info)
        count += len(chunk)
    return papers


from raw_data import ALL_CHEMS_CID


def gen_cheminfo():
    chems = []
    for cid in ALL_CHEMS_CID:
        try:
            info = dict()
            chem = pcp.Compound.from_cid(cid)
            info['cid'] = str(chem.cid)
            info['name'] = chem.iupac_name
            info['synonyms'] = [s.lower() for s in chem.synonyms]
            info['formula'] = chem.molecular_formula
            info['related'] = [] #TODO
            chems.append(info)
            print(info)
        except:
            #???
            pass

    return chems


def gen_terms(papers, chems):
    import string
    related = set()

    for paper in papers:
        print(paper['ids'][0])
        s = paper['title'] + paper['abstract']
        freq = analyze_frequency(s)
        # todo: make this better
        score = 0
        terms = set(freq.keys()).intersection(HIGH_SCORE_TERMS)
        paper['related'].extend(terms)

        s = s.lower()
        s = s.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))

        for chem in chems:
            if (overlap := set(chem['synonyms']).intersection(set(s.split()))):
                print("got a paper <> chem match",overlap)
                chem['related'].extend(overlap)
                paper['related'].extend(set(paper['related']).intersection(overlap))
            #print(chem)

def gen_edcdb():
    if os.path.exists('termsdb.json'):
        with open('termsdb.json', 'r') as f:
            papers, chems = json.load(f)
    else:
        papers = gen_paperinfo()
        chems = gen_cheminfo()
        gen_terms(papers, chems)
        with open('termsdb.json', 'w') as f:
            json.dump([papers, chems], f)
    with open('edcdb_gcp/edcdb_papers.csv', 'w') as f:
        ps = []
        for p in papers:
            if p['ids'][0].replace('pubmed:','') in DEDUCT_FINAL_PAPERS:
                ps.append(p)
        writer = csv.DictWriter(f, ['ids','pubdate','authors','title','pubtypes','journal','abstract','related'])
        writer.writeheader()
        writer.writerows(ps)
        print()
    with open('edcdb_gcp/edcdb_chems.csv', 'w') as f:
        writer = csv.DictWriter(f, ['cid','name','synonyms','formula','related'])
        writer.writeheader()
        writer.writerows(chems)
        print()



def most_common_words():
    from raw_data import EXCLUDE_TERMS
    ALL_WORDS = defaultdict(lambda : 0)
    FILTERED_WORDS = defaultdict(lambda : 0)

    count = 0
    for article in get_offline_articles_from_csv():
        count += 1
        if count%10000==0:
            print(count)
        if count > 100000:
            break
        searchable = ' '.join(article.values())
        for w in searchable.split():
            ALL_WORDS[w] += 1
        filtered = analyze_frequency(searchable)
        for k,v in filtered.items():
            FILTERED_WORDS[k] += v
            #print(k,v)


    with open('all_word_freqs.csv', 'w') as f:
        columns = ['word', 'numoccur']
        writer = csv.DictWriter(f, columns)
        writer.writeheader()
        out = reversed(sorted(ALL_WORDS.items(), key=lambda x: x[1]))
        for thing in out:
            writer.writerow({'word': thing[0],'numoccur': thing[1]})


    with open('all_word_freqs_filtered.csv', 'w') as f:
        columns = ['word', 'numoccur']
        writer = csv.DictWriter(f, columns)
        writer.writeheader()
        out = reversed(sorted(FILTERED_WORDS.items(), key=lambda x: x[1]))
        for thing in out:
            writer.writerow({'word': thing[0],'numoccur': thing[1]})

def find_best_synonyms():
    import easy_entrez
    from easy_entrez.parsing import xml_to_string
    import xmltodict
    entrez_api = easy_entrez.EntrezAPI('endoscreen', 'verditelabs@gmail.com', return_type='json')
    search_term = ''
    with open('./edcdb_gcp/edcdb.json', 'r') as f, open('./log.txt', 'w+') as logf:
        papers, chems = json.load(f)
        synonyms_to_cid = dict()
        for c in chems:
            for syn in c['synonyms'] + [c['name']]:
                if syn is None:
                    continue  # ???
                syn = syn.lower()
                if syn in synonyms_to_cid:
                    pass
                    #print("wtf!?", syn)
                synonyms_to_cid[syn] = c['cid']
                #print(syn, c['cid'])
        for syn in synonyms_to_cid:
            time.sleep(.1)
            try:
                res = entrez_api.search(syn, max_results=999, database='pubmed')
                l = str(syn)+'|||||'+str(synonyms_to_cid[syn])+'|||||'+str(len(res.data['esearchresult']['idlist'])) +'\n'
                print(l)
                logf.write(l)
            except:
                continue


banned_terms = [
        '[', ']', '%', '>', '=', '<', ';', '{', '}'  # filter out weird punctuation stuff
                                                'CAS', 'CCRIS', 'CHEBI', 'CHEMBL', 'DSSTox', 'NCGC', 'NSC', 'NCI',
        # other identifiers?
        'Caswell', 'MLS', 'MFCD', 'STL', 'Tox', 'bmse', 'EINECS', 'ENT', 'ZINC',
        'UNII', 'VS-', 'WLN', 'BDBM', 'CCG', 'CS', '_',
        'British', 'European', 'antibiotic', 'KBio', 'BPBio', 'Spectrum',
        'Prestwick', 'component', 'reference', 'ampule', 'injectable',
        'reagent', 'powder', 'tested', 'mg/mL', 'FEMA', 'BSPBio', 'United States', 'mixture',
        '(VAN)', '(1:1)', '/mL', 'byproduct', 'EPA', 'Standard', '(TN)', 'german', 'indicator',
        'biological', 'Commission', 'Pesticide', 'RCRA', '(R)', 'TraceCERT', '(alpha)', '(INN)',
        '.beta.', '.alpha.', 'diameter', 'length', 'elemental', 'metallic', 'g/g', '/', 'GRADE',
        'Nanopowder', 'Dispersion', 'Powder', 'dia', 'unpurified', '#', 'ACon', 'Lopac', 'MEGxp',
        'Biomo', 'KBio', '(TBB)', 'Reference', 'Handbook', 'Epitope', 'Rcra', 'dtxsid','en300','albb-',
    'bidd:', 'brn ', 'colloidal','molten','micronized','precipitated','sublimed',
    'contains','specially','anhydrous','sbi-','brd-k','handbook','[',']'
    ]

banned_terms = [t.lower() for t in banned_terms]
import re
def skip_synonym(syn):

    if syn is None:
        return True
    if re.match('[0-9]+\-[0-9]+\-[0-9]+', syn):
        return True #CAS IDs
    if re.match('cas\-[0-9]+\-[0-9]+\-[0-9]+', syn):
        return True #CAS IDs
    if re.match('[a-z][0-9]+',syn):
        return True #lots of random things look like this
    if re.match('akos[0-9]+',syn):
        return True
    if re.match('ai3\-[0-9]+',syn):
        return True
    if re.match('act[0-9]+',syn):
        return True
    if re.match('ac\-[0-9]+',syn):
        return True
    if re.match('smr[0-9]+',syn):
        return True
    if re.match('sr\-[0-9]+',syn):
        return True
    if re.match('sr\-[0-9]+\-[0-9]+',syn):
        return True
    if re.match('j\-[0-9]+',syn):
        return True
    if re.match('ds\-[0-9]+',syn):
        return True
    if re.match('un[0-9]+',syn):
        return True
    if re.match('un [0-9]+',syn):
        return True
    if re.match('str[0-9]+',syn):
        return True
    if re.match('stk[0-9]+',syn):
        return True
    if re.match('sb[0-9]+',syn):
        return True
    if re.match('q\-[0-9]+',syn):
        return True
    if re.match('bcp[0-9]+',syn):
        return True
    if re.match('bbl[0-9]+',syn):
        return True
    if re.match('as\-[0-9]+',syn):
        return True
    if re.match('amy[0-9]+',syn):
        return True

    asdf = [term in syn for term in banned_terms]
    return any(asdf)

def process_synonym_log():
    from collections import defaultdict
    cid_syn_map = defaultdict(lambda:[])
    with open('log.txt','r') as f:
        for line in f:
            syn,cid,score = line.split('|||||')
            print(syn, cid, score)
            if int(score) > 100: #TODO: is this a good cutoff?
                cid_syn_map[cid].append(syn)
        syns = 0
        for k,v in cid_syn_map.items():
            v = list(filter(lambda x: not skip_synonym(x),v))
            cid_syn_map[k] = v
            syns += len(v)
            print(k,v)
        print(syns)
    new_chems = list()
    with open('./edcdb_gcp/edcdb.json', 'r') as f:
        papers, chems = json.load(f)

        for chem in chems:
            if chem['cid'] not in cid_syn_map:
                new_chems.append(chem)#???
            else:
                chem['synonyms'] = cid_syn_map[chem['cid']]
                new_chems.append(chem)

                print()
    with open('./edcdb_gcp/edcdb.json', 'w') as f:
        json.dump([papers, new_chems], f)

def pubchem_data_download():
    import wget
    pubchem_url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{}/JSON/'
    with open('./edcdb_gcp/edcdb.json', 'r') as f:
        papers,chems = json.load(f)
    for chem in chems:
        url = pubchem_url.format(chem['cid'])
        path = 'data/' + chem['cid'] + 'pubchem'  + '.json'
        if os.path.exists(path):
            continue

        time.sleep(.1)
        print('wget ',url)
        wget.download(url, path)

def hsdb_data_download():
    import wget
    num_hsdb = 0
    for p in os.listdir('data'):
        with open('data/' + p,'r') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print('failed opening',p)
                print(e)
                continue
            print()
            for ref in data['Record']['Reference']:
                #print(ref)
                if 'HSDB' in ref['SourceName']:
                    url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/annotation/{}/JSON/'
                    url = url.format(ref['ANID'])
                    out = 'data/' + str(data['Record']['RecordNumber']) + 'hsdb.json'
                    print('wget',url)
                    wget.download(url,out)
                    num_hsdb+=1
    print(num_hsdb)


def parse_cheminfo():
    good_headers = {
        '11B NMR Spectra',
        '13C NMR Spectra',
        '15N NMR Spectra',
        '17O NMR Spectra',
        '19F NMR Spectra',
        '1D NMR Spectra',
        '1H NMR Spectra',
        '1H-13C NMR Spectra',
        '1H-1H NMR Spectra',
        '29Si NMR Spectra',
        '2D NMR Spectra',
        '2D Structure',
        '31P NMR Spectra',
        '3D Conformer',
        '3D Status',
        'ATC Code',
        'ATR-IR Spectra',
        'Absorption, Distribution and Excretion',
        'Absorption, Distribution and Excretion (Complete)',
        'Acceptable Daily Intakes',
        'Acceptable Daily Intakes (Complete)',
        'Accidental Release Measures',
        'Acute Effects',
        'Acute Exposure Guideline Levels (AEGLs)',
        'Acute Toxicity Link',
        'Administrative Information',
        'Adverse Effects',
        'Agrochemical Category',
        'Agrochemical Information',
        'Agrochemical Transformations',
        'Air and Water Reactions',
        'Allowable Tolerances',
        'Allowable Tolerances (Complete)',
        'Analytic Laboratory Methods',
        'Analytic Laboratory Methods (Complete)',
        'Animal Concentrations',
        'Animal Concentrations (Complete)',
        'Animal Toxicity Studies',
        'Antidote and Emergency Treatment',
        'Antidote and Emergency Treatment (Complete)',
        'Artificial Pollution Sources',
        'Artificial Pollution Sources (Complete)',
        'Associated Article',
        'Associated Chemicals',
        'Associated Chemicals (Complete)',
        'Associated Disorders and Diseases',
        'Atmospheric Concentrations',
        'Atmospheric Concentrations (Complete)',
        'Atmospheric Standards',
        'Atmospheric Standards (Complete)',
        'Atomic Number',
        'Autoignition Temperature',
        'Average Daily Intake',
        'Average Daily Intake (Complete)',
        'BioAssay Results',
        'Biochemical Reactions',
        'Biologic Depiction',
        'Biologic Description',
        'Biologic Line Notation',
        'Biological Half-Life',
        'Biological Half-Life (Complete)',
        'Biological Test Results',
        'Biomarker Information',
        'Bionecessity',
        'Bionecessity (Complete)',
        'Body Burden',
        'Body Burden (Complete)',
        'Boiling Point',
        'CAMEO Chemicals',
        'CAS',
        'CCDC Number',
        'CCS Classification - Baker Lab',
        'CCSBase Classification',
        'CERCLA Reportable Quantities',
        'CERCLA Reportable Quantities (Complete)',
        'Caco2 Permeability',
        'Cancer Drugs',
        'Cancer Sites',
        'Canonical SMILES',
        'Carcinogen Classification',
        'Cellular Locations',
        'ChEBI Ontology',
        'ChEMBL Target Tree',
        'ChemIDplus',
        'Chemical Classes',
        'Chemical Co-Occurrences in Literature',
        'Chemical Safety',
        'Chemical Safety & Handling',
        'Chemical Vendors',
        'Chemical and Physical Properties',
        'Chemical-Disease Co-Occurrences in Literature',
        'Chemical-Gene Co-Occurrences in Literature',
        'Chemical-Target Interactions',
        'Chemical/Physical Properties',
        'Classification',
        'Clean Water Act Requirements',
        'Cleanup Methods',
        'Cleanup Methods (Complete)',
        'Clinical Laboratory Methods',
        'Clinical Laboratory Methods (Complete)',
        'Clinical Trials',
        'ClinicalTrials.gov',
        'Collision Cross Section',
        'Color Additive Status',
        'Color/Form',
        'Color/Form (Complete)',
        'Complexity',
        'Component Compounds',
        'Compound Is Canonicalized',
        'Computed Descriptors',
        'Computed Properties',
        'Consumer Product Information Database Classification',
        'Consumer Uses',
        'Consumption Patterns',
        'Consumption Patterns (Complete)',
        'Corrosivity',
        'Covalently-Bonded Unit Count',
        'Create Date',
        'Critical Temperature & Pressure',
        'Crystal Structure Data',
        'Crystal Structures',
        'DEA Code Number',
        'DEA Controlled Substances',
        'DEA Drug Facts',
        'DOT Emergency Guidelines',
        'DOT Emergency Guidelines (Complete)',
        'DOT ID and Guide',
        'DOT Label',
        'DSSTox Substance ID',
        'Decomposition',
        'Defined Atom Stereocenter Count',
        'Defined Bond Stereocenter Count',
        'Density',
        'Depositor Provided PubMed Citations',
        'Depositor-Supplied Patent Identifiers',
        'Depositor-Supplied Synonyms',
        'Deprecated CAS',
        'Dielectric Constant',
        'Disease and References',
        'Dispersion',
        'Disposal Methods',
        'Disposal Methods (Complete)',
        'Dissociation Constants',
        'Drug Classes',
        'Drug Effects during Lactation',
        'Drug Enforcement Administration (DEA) Classification',
        'Drug Idiosyncrasies',
        'Drug Indication',
        'Drug Induced Liver Injury',
        'Drug Labels for Ingredients',
        'Drug Tolerance',
        'Drug Transformations',
        'Drug Warnings',
        'Drug Warnings (Complete)',
        'Drug and Medication Information',
        'Drug-Drug Interactions',
        'Drug-Food Interactions',
        'EC Classification',
        'EMA Drug Information',
        'EPA CPDat Classification',
        'EPA DSSTox Classification',
        'EPA Ecotoxicity',
        'EPA Hazardous Waste Number',
        'EPA Safer Chemical',
        'EPA Safer Choice',
        'EPA Substance Registry Services Tree',
        'EU Clinical Trials Register',
        'EU Pesticides Data',
        'Ecological Information',
        'Ecotoxicity Excerpts',
        'Ecotoxicity Excerpts (Complete)',
        'Ecotoxicity Values',
        'Ecotoxicity Values (Complete)',
        'Effects of Long Term Exposure',
        'Effects of Short Term Exposure',
        'Effluent Concentrations',
        'Effluent Concentrations (Complete)',
        'Element Name',
        'Element Symbol',
        'Emergency Medical Treatment',
        'Emergency Response Planning Guidelines',
        'Emergency Response Planning Guidelines (Complete)',
        'Enthalpy of Sublimation',
        'Entrez Crosslinks',
        'Environmental Abiotic Degradation',
        'Environmental Abiotic Degradation (Complete)',
        'Environmental Bioconcentration',
        'Environmental Bioconcentration (Complete)',
        'Environmental Biodegradation',
        'Environmental Biodegradation (Complete)',
        'Environmental Fate',
        'Environmental Fate & Exposure',
        'Environmental Fate (Complete)',
        'Environmental Fate/Exposure Summary',
        'Environmental Standards & Regulations',
        'Environmental Water Concentrations',
        'Environmental Water Concentrations (Complete)',
        'European Community (EC) Number',
        'Evaluations of the Joint FAO/WHO Expert Committee on Food Additives - JECFA',
        'Evidence for Carcinogenicity',
        'Evidence for Carcinogenicity (Complete)',
        'Exact Mass',
        'Experimental Properties',
        'Explosion Hazards',
        'Explosive Limits and Potential',
        'Explosive Limits and Potential (Complete)',
        'Exposure Control and Personal Protection',
        'Exposure Prevention',
        'Exposure Routes',
        'Eye First Aid',
        'Eye Prevention',
        'Eye Symptoms',
        'FDA Drug Type and Pharmacologic Classification',
        'FDA Generally Recognized as Safe - GRAS Notices',
        'FDA Green Book',
        'FDA Indirect Additives used in Food Contact Substances',
        'FDA Inventory of Effective Food Contact Substance Notifications - FCN',
        'FDA Medication Guides',
        'FDA National Drug Code Directory',
        'FDA Orange Book',
        'FDA Orange Book Patents',
        'FDA Pharm Classes',
        'FDA Pharmacological Classification',
        'FDA Requirements',
        'FDA Requirements (Complete)',
        'FDA Substances Added to Food',
        'FEMA Flavor Profile',
        'FEMA Number',
        'FIFRA Requirements',
        'FIFRA Requirements (Complete)',
        'FTIR Spectra',
        'Federal Drinking Water Guidelines',
        'Federal Drinking Water Standards',
        'Federal Drinking Water Standards (Complete)',
        'Fire Fighting',
        'Fire Fighting Procedures',
        'Fire Fighting Procedures (Complete)',
        'Fire Hazards',
        'Fire Potential',
        'Fire Prevention',
        'Firefighting Hazards',
        'Firefighting Hazards (Complete)',
        'First Aid',
        'First Aid Measures',
        'Fish/Seafood Concentrations',
        'Fish/Seafood Concentrations (Complete)',
        'Flammable Limits',
        'Flash Point',
        'Food Additive Classes',
        'Food Additive Definition',
        'Food Additive Status',
        'Food Additives and Ingredients',
        'Food Survey Values',
        'Food Survey Values (Complete)',
        'Formal Charge',
        'Formulations/Preparations',
        'Formulations/Preparations (Complete)',
        'GC-MS',
        'GHS Classification',
        'General Manufacturing Information',
        'General Manufacturing Information (Complete)',
        'General References',
        'GlyCosmos Monoisotopic Mass',
        'GlyCosmos Subsumption',
        'GlyTouCan Accession',
        'HIV/AIDS and Opportunistic Infection Drugs',
        'HSDB Note',
        'Handling and Storage',
        'Hazard Classes and Categories',
        'Hazardous Reactivities and Incompatibilities',
        'Hazardous Reactivities and Incompatibilities (Complete)',
        'Hazardous Substances DataBank Number',
        'Hazards Identification',
        'Hazards Summary',
        'Health Effects',
        'Health Hazards',
        'Heat of Combustion',
        'Heat of Vaporization',
        'Heavy Atom Count',
        "Henry's Law Constant",
        'Hepatotoxicity',
        'Highly Hazardous Substance',
        'History and Incidents',
        'History and Incidents (Complete)',
        'Household Products',
        'Human Health Effects',
        'Human Metabolite Information',
        'Human Toxicity Excerpts',
        'Human Toxicity Excerpts (Complete)',
        'Human Toxicity Values',
        'Human Toxicity Values (Complete)',
        'Hydrogen Bond Acceptor Count',
        'Hydrogen Bond Donor Count',
        'ICSC Environmental Data',
        'ICSC Number',
        'IR Spectra',
        'IUPAC Name',
        'IUPHAR/BPS Guide to PHARMACOLOGY Target Classification',
        'Identification',
        'Immediately Dangerous to Life or Health (IDLH)',
        'Impurities',
        'Impurities (Complete)',
        'InChI',
        'InChIKey',
        'Industry Uses',
        'Ingestion First Aid',
        'Ingestion Prevention',
        'Ingestion Symptoms',
        'Inhalation First Aid',
        'Inhalation Prevention',
        'Inhalation Risk',
        'Inhalation Symptoms',
        'Interactions',
        'Interactions (Complete)',
        'Interactions and Pathways',
        'International Agency for Research on Cancer (IARC) Classification',
        'Ionization Efficiency',
        'Ionization Potential',
        'Isolation and Evacuation',
        'Isomeric SMILES',
        'Isotope Atom Count',
        'JECFA Number',
        'KEGG : Antimicrobials',
        'KEGG : Antimicrobials Abbreviations',
        'KEGG : Glycosides',
        'KEGG: ATC',
        'KEGG: Animal Drugs',
        'KEGG: Drug',
        'KEGG: Drug Classes',
        'KEGG: Drug Groups',
        'KEGG: EDC',
        'KEGG: JP15',
        'KEGG: Lipid',
        'KEGG: Metabolite',
        'KEGG: Natural Toxins',
        'KEGG: OTC drugs',
        'KEGG: Pesticides',
        'KEGG: Phytochemical Compounds',
        'KEGG: Risk Category of Japanese OTC Drugs',
        'KEGG: Target-based Classification of Drugs',
        'KEGG: USP',
        'Kovats Retention Index',
        'LC-MS',
        'LIPID MAPS Classification',
        'LOTUS Tree',
        'Label Download',
        'Label Image',
        'Label Ingredient',
        'Label Title',
        'Laboratory Methods',
        'Last Review Date',
        'Last Revision Date',
        'Ligands from Protein Bound 3D Structures',
        'Literature',
        'LiverTox Summary',
        'LogP',
        'LogS',
        'Lower Explosive Limit (LEL)',
        'MALDI',
        'MS-MS',
        'Manufacturers',
        'Manufacturing/Use Information',
        'Mass Spectrometry',
        'Maximum Drug Dose',
        'MeSH Entry Terms',
        'MeSH Pharmacological Classification',
        'MeSH Tree',
        'Mechanism of Action',
        'Mechanism of Action (Complete)',
        'Medical Surveillance',
        'Medical Surveillance (Complete)',
        'Melting Point',
        'Metabolism/ Pharmacokinetics',
        'Metabolism/Metabolites',
        'Metabolism/Metabolites (Complete)',
        'Metabolite Pathways',
        'Metabolite References',
        'Metabolomics Workbench ID',
        'Methods of Manufacturing',
        'Methods of Manufacturing (Complete)',
        'Milk Concentrations',
        'Milk Concentrations (Complete)',
        'Minerals',
        'Minimum Risk Level',
        'Modify Date',
        'Molecular Formula',
        'Molecular Weight',
        'Monoisotopic Mass',
        'NCBI LinkOut',
        'NCI Thesaurus Code',
        'NCI Thesaurus Tree',
        'NDC Code(s)',
        'NFPA Hazard Classification',
        'NIOSH Analytical Methods',
        'NIOSH Recommendations',
        'NIOSH Recommendations (Complete)',
        'NIOSH Toxicity Data',
        'NIPH Clinical Trials Search of Japan',
        'NIST Synthetic Polymer MALDI Recipes Database Classification',
        'NLM Curated PubMed Citations',
        'NORMAN Suspect List Exchange Classification',
        'NSC Number',
        'Names and Identifiers',
        'National Toxicology Program Studies',
        'National Toxicology Program Studies (Complete)',
        'Natural Pollution Sources',
        'Natural Pollution Sources (Complete)',
        'Near IR Spectra',
        'Nikkaji Number',
        'Non-Human Toxicity Excerpts',
        'Non-Human Toxicity Excerpts (Complete)',
        'Non-Human Toxicity Values',
        'Non-Human Toxicity Values (Complete)',
        'Nonfire Spill Response',
        'OSHA Standards',
        'OSHA Standards (Complete)',
        'Occupational Exposure Standards',
        'Odor',
        'Odor Threshold',
        'Odor Threshold (Complete)',
        'Ongoing Test Status',
        'Optical Rotation',
        'Other Environmental Concentrations',
        'Other Environmental Concentrations (Complete)',
        'Other Experimental Properties',
        'Other Experimental Properties (Complete)',
        'Other Hazardous Reactions',
        'Other Identifiers',
        'Other MS',
        'Other Relationships',
        'Other Safety Information',
        'Other Spectra',
        'Other Standards Regulations and Guidelines',
        'Other Standards Regulations and Guidelines (Complete)',
        'PFAS and Fluorinated Organic Compounds in PubChem',
        'Packager',
        'Packaging and Labelling',
        'Parent Compound',
        'Patents',
        'Pathways',
        'Permissible Exposure Limit (PEL)',
        'Peroxide Forming Chemical',
        'Personal Protective Equipment (PPE)',
        'Personal Protective Equipment (PPE) (Complete)',
        'Pharmacodynamics',
        'Pharmacology',
        'Pharmacology and Biochemistry',
        'Physical Dangers',
        'Physical Description',
        'Plant Concentrations',
        'Plant Concentrations (Complete)',
        'Polymerization',
        'Populations at Special Risk',
        'Populations at Special Risk (Complete)',
        'Preventive Measures',
        'Preventive Measures (Complete)',
        'Probable Routes of Human Exposure',
        'Probable Routes of Human Exposure (Complete)',
        'Protein Binding',
        'Protein Bound 3D Structures',
        'RCRA Requirements',
        'RCRA Requirements (Complete)',
        'RTECS Number',
        'RXCUI',
        'Radiation Limits and Potential',
        'Radiation Limits and Potential (Complete)',
        'Raman Spectra',
        'Reactive Group',
        'Reactivity Alerts',
        'Reactivity Profile',
        'Recommended Exposure Limit (REL)',
        'Record Description',
        'Refractive Index',
        'Regulatory Information',
        'Related CAS',
        'Related Compounds',
        'Related Compounds with Annotation',
        'Related Element',
        'Related HSDB Records',
        'Related PubChem Records',
        'Related Records',
        'Related Substances',
        'Relative Evaporation Rate',
        'Removed Synonyms',
        'Reported Fatal Dose',
        'Respirator Recommendations',
        'Rotatable Bond Count',
        'Safe Storage',
        'Safety and Hazard Properties',
        'Safety and Hazards',
        'Sampling Procedures',
        'Sampling Procedures (Complete)',
        'Sediment/Soil Concentrations',
        'Sediment/Soil Concentrations (Complete)',
        'Shipment Methods and Regulations',
        'Shipment Methods and Regulations (Complete)',
        'Shipping Name/ Number DOT/UN/NA/IMO',
        'Shipping Name/ Number DOT/UN/NA/IMO (Complete)',
        'Skin First Aid',
        'Skin Prevention',
        'Skin Symptoms',
        'Skin, Eye, and Respiratory Irritations',
        'Soil Adsorption/Mobility',
        'Soil Adsorption/Mobility (Complete)',
        'Solubility',
        'Solubility (Complete)',
        'Special References',
        'Special Reports',
        'Special Reports (Complete)',
        'Spectral Information',
        'Spillage Disposal',
        'Springer Nature References',
        'SpringerMaterials Properties',
        'Stability and Reactivity',
        'Stability/Shelf Life',
        'Stability/Shelf Life (Complete)',
        'Standard Transportation Number',
        'State Drinking Water Guidelines',
        'State Drinking Water Guidelines (Complete)',
        'State Drinking Water Standards',
        'State Drinking Water Standards (Complete)',
        'Storage Conditions',
        'Storage Conditions (Complete)',
        'Structures',
        'Substance Title',
        'Substances',
        'Substances by Category',
        'Surface Tension',
        'Symptoms',
        'Synonyms',
        'Synonyms and Identifiers',
        'Synthesis References',
        'TSCA Requirements',
        'TSCA Test Submissions',
        'TSCA Test Submissions (Complete)',
        'Target Organs',
        'Taste',
        'Taxonomy',
        'The Natural Products Atlas Classification',
        'Therapeutic Uses',
        'Therapeutic Uses (Complete)',
        'Thieme References',
        'Threshold Limit Values (TLV)',
        'Threshold Limit Values (TLV) (Complete)',
        'Tissue Locations',
        'Topological Polar Surface Area',
        'Toxic Combustion Products',
        'Toxicity',
        'Toxicity Data',
        'Toxicity Summary',
        'Toxicological Information',
        'Transformations',
        'Transport Information',
        'Treatment',
        'U.S. Exports',
        'U.S. Exports (Complete)',
        'U.S. Imports',
        'U.S. Imports (Complete)',
        'U.S. Production',
        'U.S. Production (Complete)',
        'UN Classification',
        'UN GHS Classification',
        'UN Number',
        'UNII',
        'US EPA Regional Removal Management Levels for Chemical Contaminants',
        'US EPA Regional Screening Levels for Chemical Contaminants',
        'USDA Pesticide Data Program',
        'UV Spectra',
        'UV-VIS Spectra',
        'Undefined Atom Stereocenter Count',
        'Undefined Bond Stereocenter Count',
        'Update History',
        'Upper Explosive Limit (UEL)',
        'Use Classification',
        'Use and Manufacturing',
        'Uses',
        'Uses (Complete)',
        'Vapor Density',
        'Vapor Phase IR Spectra',
        'Vapor Pressure',
        'Viscosity',
        'Volatilization from Water/Soil',
        'Volatilization from Water/Soil (Complete)',
        'WHO ATC Classification System',
        'WHO Essential Medicines',
        'WIPO PATENTSCOPE',
        'Wikidata',
        'Wikipedia',
        'Wiley References',
        'XLogP3',
        'pH',
    }
    out =dict()
    headings = set()
    for p in sorted(os.listdir('data')):
        with open('data/' + p,'r') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print("couldn't open",p)
                print(e)
                continue
        cid = p.replace('hsdb.json','').replace('pubchem.json','')
        if cid not in out:
            out[cid] = defaultdict(lambda: [])

        for s1 in data['Record']['Section']:
            headings.add(s1['TOCHeading'])
            if 'Information' in s1:
                for info in s1['Information']:
                    v = info['Value']
                    if not 'StringWithMarkup' in v:
                        continue
                    strs = [_['String'] for _ in v['StringWithMarkup']]
                    heading = s1['TOCHeading'].replace(' (Complete)','')
                    out[cid][heading].extend(strs)
            if 'Section' not in s1:
                continue
            if 'Description' in s1:
                pass
                #print()

            for s2 in s1['Section']:
                headings.add(s2['TOCHeading'])
                if 'Information' in s2:
                    for info in s2['Information']:
                        v = info['Value']
                        if not 'StringWithMarkup' in v:
                            continue
                        strs = [_['String'] for _ in v['StringWithMarkup']]
                        heading = s2['TOCHeading'].replace(' (Complete)','')
                        out[cid][heading].extend(strs)
                if 'Section' not in s2:
                    continue
                if 'Description' in s2:
                    #print()
                    pass
                for s3 in s2['Section']:
                    headings.add(s3['TOCHeading'])
                    if 'Information' in s3:
                        for info in s3['Information']:
                            v = info['Value']
                            if not 'StringWithMarkup' in v:
                               continue
                            strs = [_['String'] for _ in v['StringWithMarkup']]
                            heading = s3['TOCHeading'].replace(' (Complete)','')
                            out[cid][heading].extend(strs)
                    if 'Decription' in s3:
                        #print()
                        pass


    #print(out)
    for cid in out:
        if cid != '26042':
            continue
        print(cid)
        for header in sorted(out[cid]):
            print('\t',header)
            for v in out[cid][header]:
                v = v.replace('\t',' ')
                v = v.replace('\n',' ')
                print('\t\t',v)

    for h in headings:
        print(h)
    print(len(headings))

def parse_ghs(s):
    s = s.replace(',','')
    s = s.replace('and','')
    mapping = {
        'H200': 'Unstable explosive',
        'H201': 'Explosive: mass explosion hazard',
        'H202': 'Explosive: severe projection hazard',
        'H203': 'Explosive: fire, blast or projection hazard',
        'H204': 'Fire or projection hazard',
        'H205': 'May mass explode in fire',
        'H206': 'Fire, blast or projection hazard: increased risk of explosion if desensitizing agent is reduced',
        'H207': 'Fire or projection hazard; increased risk of explosion if desensitizing agent is reduced',
        'H208': 'Fire hazard; increased risk of explosion if desensitizing agent is reduced',
        'H209': 'Explosive',
        'H210': 'Very sensitive',
        'H211': 'May be sensitive',
        'H220': 'Extremely flammable gas',
        'H221': 'Flammable gas',
        'H222': 'Extremely flammable material',
        'H223': 'Flammable material',
        'H224': 'Extremely flammable liquid and vapour',
        'H225': 'Highly flammable liquid and vapour',
        'H226': 'Flammable liquid and vapour',
        'H227': 'Combustible liquid',
        'H228': 'Flammable solid',
        'H229': 'Pressurized container: may burst if heated',
        'H230': 'May react explosively even in the absence of air',
        'H231': 'May react explosively even in the absence of air at elevated pressure and/or temperature',
        'H240': 'Heating may cause an explosion',
        'H241': 'Heating may cause a fire or explosion',
        'H242': 'Heating may cause a fire',
        'H250': 'Catches fire spontaneously if exposed to air',
        'H251': 'Self-heating: may catch fire',
        'H252': 'Self-heating in large quantities: may catch fire',
        'H260': 'In contact with water releases flammable gases which may ignite spontaneously',
        'H261': 'In contact with water releases flammable gas',
        'H270': 'May cause or intensify fire: oxidizer',
        'H271': 'May cause fire or explosion: strong oxidizer',
        'H272': 'May intensify fire: oxidizer',
        'H280': 'Contains gas under pressure: may explode if heated',
        'H281': 'Contains refrigerated gas: may cause cryogenic burns or injury',
        'H282': 'Extremely flammable chemical under pressure: May explode if heated',
        'H283': 'Flammable chemical under pressure: May explode if heated',
        'H284': 'Chemical under pressure: May explode if heated',
        'H290': 'May be corrosive to metals',
        'H300': 'Fatal if swallowed',
        'H300+H310': 'Fatal if swallowed or in contact with skin',
        'H300+H310+H330': 'Fatal if swallowed, in contact with skin or if inhaled',
        'H300+H330': 'Fatal if swallowed or if inhaled',
        'H301': 'Toxic if swallowed',
        'H301+H311': 'Toxic if swallowed or in contact with skin',
        'H301+H311+H331': 'Toxic if swallowed, in contact with skin or if inhaled',
        'H301+H331': 'Toxic if swallowed or if inhaled',
        'H302': 'Harmful if swallowed',
        'H302+H312': 'Harmful if swallowed or in contact with skin',
        'H302+H312+H332': 'Harmful if swallowed, in contact with skin or if inhaled',
        'H302+H332': 'Harmful if swallowed or inhaled',
        'H303': 'May be harmful if swallowed',
        'H303+H313': 'May be harmful if swallowed or in contact with skin',
        'H303+H313+H333': 'May be harmful if swallowed, in contact with skin or if inhaled',
        'H303+H333': 'May be harmful if swallowed or if inhaled',
        'H304': 'May be fatal if swallowed and enters airways',
        'H305': 'May be harmful if swallowed and enters airways',
        'H310': 'Fatal in contact with skin',
        'H310+H330': 'Fatal in contact with skin or if inhaled',
        'H311': 'Toxic in contact with skin',
        'H311+H331': 'Toxic in contact with skin or if inhaled',
        'H312': 'Harmful in contact with skin',
        'H312+H332': 'Harmful in contact with skin or if inhaled',
        'H313': 'May be harmful in contact with skin',
        'H313+H333': 'May be harmful in contact with skin or if inhaled',
        'H314': 'Causes severe skin burns and eye damage',
        'H315': 'Causes skin irritation',
        'H315+H320': 'Causes skin and eye irritation',
        'H316': 'Causes mild skin irritation',
        'H317': 'May cause an allergic skin reaction',
        'H318': 'Causes serious eye damage',
        'H319': 'Causes serious eye irritation',
        'H320': 'Causes eye irritation',
        'H330': 'Fatal if inhaled',
        'H331': 'Toxic if inhaled',
        'H332': 'Harmful if inhaled',
        'H333': 'May be harmful if inhaled',
        'H334': 'May cause allergy or asthma symptoms or breathing difficulties if inhaled',
        'H335': 'May cause respiratory irritation',
        'H336': 'May cause drowsiness or dizziness',
        'H340': 'May cause genetic defects',
        'H341': 'Suspected of causing genetic defects',
        'H350': 'May cause cancer',
        'H350i': 'May cause cancer by inhalation',
        'H351': 'Suspected of causing cancer',
        'H360': 'May damage fertility or the unborn child',
        'H360D': 'May damage the unborn child',
        'H360Df': 'May damage the unborn child. Suspected of damaging fertility.',
        'H360F': 'May damage fertility',
        'H360FD': 'May damage fertility. May damage the unborn child.',
        'H360Fd': 'May damage fertility. Suspected of damaging the unborn child.',
        'H361': 'Suspected of damaging fertility or the unborn child',
        'H361d': 'Suspected of damaging the unborn child',
        'H361f': 'Suspected of damaging fertility',
        'H361fd': 'Suspected of damaging fertility. Suspected of damaging the unborn child.',
        'H362': 'May cause harm to breast-fed children',
        'H370': 'Causes damage to organs',
        'H371': 'May cause damage to organs',
        'H372': 'Causes damage to organs through prolonged or repeated exposure',
        'H373': 'May cause damage to organs through prolonged or repeated exposure ',
        'H400': 'Very toxic to aquatic life',
        'H401': 'Toxic to aquatic life',
        'H402': 'Harmful to aquatic life',
        'H410': 'Very toxic to aquatic life with long lasting effects',
        'H411': 'Toxic to aquatic life with long lasting effects',
        'H412': 'Harmful to aquatic life with long lasting effects',
        'H413': 'May cause long lasting harmful effects to aquatic life',
        'H420': 'Harms public health and the environment by destroying ozone in the upper atmosphere',
        'H441': 'Very toxic to terrestrial invertebrates',
        'P101': 'If medical advice is needed, have product container or label at hand.',
        'P102': 'Keep out of reach of children.',
        'P103': 'Read carefully and follow all instructions.',
        'P201': '(Obsolete) Obtain special instructions before use.',
        'P202': '(Obsolete) Do not handle until all safety precautions have been read and understood.',
        'P203': 'Obtain, read and follow all safety instructions before use.',
        'P210': 'Keep away from heat, hot surface, sparks, open flames and other ignition sources. No smoking.',
        'P211': 'Do not spray on an open flame or other ignition source.',
        'P212': 'Avoid heating under confinement or reduction of the desensitized agent.',
        'P220': 'Keep away from clothing and other combustible materials.',
        'P221': '(Obsolete) Take any precaution to avoid mixing with combustibles/...',
        'P222': 'Do not allow contact with air.',
        'P223': 'Do not allow contact with water.',
        'P230': 'Keep wetted with ...',
        'P231': 'Handle and store contents under inert gas/...',
        'P232': 'Protect from moisture.',
        'P233': 'Keep container tightly closed.',
        'P234': 'Keep only in original container.',
        'P235': 'Keep cool.',
        'P236': 'Keep only in original packaging; Division .. in the transport configuraion.',
        'P240': 'Ground/bond container and receiving equipment.',
        'P241': 'Use explosion-proof [electrical/ventilating/lighting/.../] equipment.',
        'P242': 'Use only non-sparking tools.',
        'P243': 'Take precautionary measures against static discharge.',
        'P244': 'Keep valves and fittings free from oil and grease.',
        'P250': 'Do not subject to grinding/shock/friction/...',
        'P251': 'Do not pierce or burn, even after use.',
        'P260': 'Do not breathe dust/fume/gas/mist/vapors/spray.',
        'P261': 'Avoid breathing dust/fume/gas/mist/vapors/spray.',
        'P262': 'Do not get in eyes, on skin, or on clothing.',
        'P263': 'Avoid contact during pregnancy/while nursing.',
        'P264': 'Wash hands [and …] thoroughly after handling.',
        'P265': 'Do not touch eyes.',
        'P270': 'Do not eat, drink or smoke when using this product.',
        'P271': 'Use only outdoors or in a well-ventilated area.',
        'P272': 'Contaminated work clothing should not be allowed out of the workplace.',
        'P273': 'Avoid release to the environment.',
        'P280': 'Wear protective gloves/protective clothing/eye protection/face protection/hearing protection/...',
        'P281': '(Obsolete)Use personal protective equipment as required.',
        'P282': 'Wear cold insulating glovesand either face shield or eye protection.',
        'P283': 'Wear fire resistant or flame retardant clothing.',
        'P284': '[In case of inadequate ventilation] Wear respiratory protection.',
        'P285': '(Obsolete) In case of inadequate ventilation wear respiratory protection.',
        'P231+P232': 'Handle and store contents under inert gas/... Protect from moisture.',
        'P264+P265': 'Wash hands [and …] thoroughly after handling. Do not touch eyes.',
        'P235+P410': '(Obsolete) Keep cool. Protect from sunlight.',
        'P301': 'IF SWALLOWED:',
        'P302': 'IF ON SKIN:',
        'P303': 'IF ON SKIN (or hair):',
        'P304': 'IF INHALED:',
        'P305': 'IF IN EYES:',
        'P306': 'IF ON CLOTHING:',
        'P307': '(Obsolete) IF exposed:',
        'P308': 'IF exposed or concerned:',
        'P309': '(Obsolete) IF exposed or if you feel unwell',
        'P310': '(Obsolete) Immediately call a POISON CENTER or doctor/physician.',
        'P311': '(Obsolete) Call a POISON CENTER or doctor/...',
        'P312': '(Obsolete) Call a POISON CENTER or doctor/... if you feel unwell.',
        'P313': '(Obsolete) Get medical advice/attention.',
        'P314': '(Obsolete) Get medical advice/attention if you feel unwell.',
        'P315': '(Obsolete) Get immediate medical advice/attention.',
        'P316': 'Get emergency medical help immediately.',
        'P317': 'Get emergency medical help.',
        'P318': 'if exposed or concerned, get medical advice.',
        'P319': 'Get medical help if you feel unwell.',
        'P320': 'Specific treatment is urgent (see ... on this label).',
        'P321': 'Specific treatment (see ... on this label).',
        'P322': '(Obsolete) Specific measures (see ...on this label).',
        'P330': 'Rinse mouth.',
        'P331': 'Do NOT induce vomiting.',
        'P332': 'IF SKIN irritation occurs:',
        'P333': 'If skin irritation or rash occurs:',
        'P334': 'Immerse in cool water [or wrap in wet bandages].',
        'P335': 'Brush off loose particles from skin.',
        'P336': 'Thaw frosted parts with lukewarm water. Do not rub affected area.',
        'P337': 'If eye irritation persists:',
        'P338': 'Remove contact lenses, if present and easy to do. Continue rinsing.',
        'P340': 'Remove person to fresh air and keep comfortable for breathing.',
        'P341': '(Obsolete) If breathing is difficult, remove victim to fresh air and keep at rest in a position comfortable for breathing.',
        'P342': 'If experiencing respiratory symptoms:',
        'P350': '(Obsolete) Gently wash with plenty of soap and water.',
        'P351': 'Rinse cautiously with water for several minutes.',
        'P352': 'Wash with plenty of water/...',
        'P353': 'Rinse skin with water [or shower].',
        'P354': 'Immediately rinse with water for several minutes.',
        'P360': 'Rinse immediately contaminated clothing and skin with plenty of water before removing clothes.',
        'P361': 'Take off immediately all contaminated clothing.',
        'P362': 'Take off contaminated clothing.',
        'P363': 'Wash contaminated clothing before reuse.',
        'P364': 'And wash it before reuse.',
        'P370': 'In case of fire:',
        'P371': 'In case of major fire and large quantities:',
        'P372': 'Explosion risk.',
        'P373': 'DO NOT fight fire when fire reaches explosives.',
        'P374': '(Obsolete) Fight fire with normal precautions from a reasonable distance.',
        'P375': 'Fight fire remotely due to the risk of explorsion.',
        'P376': 'Stop leak if safe to do so.',
        'P377': 'Leaking gas fire: Do not extinguish, unless leak can be stopped safely.',
        'P378': 'Use ... to extinguish.',
        'P380': 'Evacuate area.',
        'P381': 'In case of leakage, eliminate all ignition sources.',
        'P390': 'Absorb spillage to prevent material damage.',
        'P391': 'Collect spillage.',
        'P301+P310': '(Obsolete) IF SWALLOWED: Immediately call a POISON CENTER/doctor/...',
        'P301+P312': '(Obsolete) IF SWALLOWED: call a POISON CENTER/doctor/... IF you feel unwell.',
        'P301+P316': 'IF SWALLOWED: Get emergency medical help immediately.',
        'P301+P317': 'IF SWALLOWED: Get medical help.',
        'P301+P330+P331': 'IF SWALLOWED: Rinse mouth. Do NOT induce vomiting.',
        'P302+P317': 'IF ON SKIN: Get medical help.',
        'P302+P334': 'IF ON SKIN: Immerse in cool water or wrap in wet bandages.',
        'P302+P335+P334': 'Brush off loose particles from skin. Immerse in cool water [or wrap in wet bandages].',
        'P302+P350': '(Obsolete) IF ON SKIN: Gently wash with plenty of soap and water.',
        'P302+P352': 'IF ON SKIN: wash with plenty of water/...',
        'P302+P361+P354': 'IF ON SKIN: Take off Immediately all contaminated clothing. Immediately rinse with water for several minutes.',
        'P303+P361+P353': 'IF ON SKIN (or hair): Take off Immediately all contaminated clothing. Rinse SKIN with water [or shower].',
        'P304+P312': '(Obsolete) IF INHALED: Call a POISON CENTER/doctor/... if you feel unwell.',
        'P304+P317': 'IF INHALED: Get medical help.',
        'P304+P340': 'IF INHALED: Remove person to fresh air and keep comfortable for breathing.',
        'P304+P341': '(Obsolete) IF INHALED: If breathing is difficult, remove victim to fresh air and keep at rest in a position comfortable for breathing.',
        'P305+P351+P338': 'IF IN EYES: Rinse cautiously with water for several minutes. Remove contact lenses if present and easy to do - continue rinsing.',
        'P305+P354+P338': 'IF IN EYES: Immediately rinse with water for several minutes. Remove contact lenses if present and easy to do. Continue rinsing.',
        'P306+P360': 'IF ON CLOTHING: Rinse Immediately contaminated CLOTHING and SKIN with plenty of water before removing clothes.',
        'P308+P316': 'IF exposed or concerned: Get emergency medical help immediately.',
        'P307+P311': '(Obsolete) IF exposed: call a POISON CENTER or doctor/physician.',
        'P308+P311': '(Obsolete) IF exposed or concerned: Call a POISON CENTER/doctor/...',
        'P308+P313': '(Obsolete) IF exposed or concerned: Get medical advice/attention.',
        'P309+P311': '(Obsolete) IF exposed or if you feel unwell: call a POISON CENTER or doctor/physician.',
        'P332+P313': '(Obsolete) IF SKIN irritation occurs: Get medical advice/attention.',
        'P332+P317': 'If skin irritation occurs: Get medical help.',
        'P333+P317': 'If skin irritation or rash occurs: Get medical help.',
        'P336+P317': 'Immediately thaw frosted parts with lukewarm water. Do not rub affected area. Get medical help.',
        'P337+P317': 'If eye irritation persists: Get medical help.',
        'P342+P316': 'If experiencing respiratory symptoms: Get emergence medical help immediately.',
        'P333+P313': '(Obsolete) IF SKIN irritation or rash occurs: Get medical advice/attention.',
        'P335+P334': '(Obsolete) Brush off loose particles from skin. Immerse in cool water/wrap in wet bandages.',
        'P337+P313': '(Obsolete) IF eye irritation persists: Get medical advice/attention.',
        'P342+P311': '(Obsolete) IF experiencing respiratory symptoms: Call a POISON CENTER/doctor/...',
        'P361+P364': 'Take off immediately all contaminated clothing and wash it before reuse.',
        'P362+P364': 'Take off contaminated clothing and wash it before reuse.',
        'P370+P376': 'in case of fire: Stop leak if safe to do so.',
        'P370+P378': 'In case of fire: Use ... to extinguish.',
        'P370+P380': '(Obsolete) In case of fire: Evacuate area.',
        'P370+P380+P375': 'In case of fire: Evacuate area. Fight fire remotely due to the risk of explosion.',
        'P371+P380+P375': 'In case of major fire and large quantities: Evacuate area. Fight fire remotely due to the risk of explosion.',
        'P370+P372+P380+P373': 'In case of fire: Explosion risk. Evacuate area. DO NOT fight fire when fire reaches explosives.',
        'P370+P380+P375[+P378]': 'In case of fire: Evacuate area. Fight fire remotely due to the risk of explosion. [Use…to extinguish].]',
        'P401': 'Store in accordance with ...',
        'P402': 'Store in a dry place.',
        'P403': 'Store in a well-ventilated place.',
        'P404': 'Store in a closed container.',
        'P405': 'Store locked up.',
        'P406': 'Store in corrosive resistant/... container with a resistant inner liner.',
        'P407': 'Maintain air gap between stacks or pallets.',
        'P410': 'Protect from sunlight.',
        'P411': 'Store at temperatures not exceeding ... °C/...°F.',
        'P412': 'Do not expose to temperatures exceeding 50 °C/ 122 °F.',
        'P413': 'Store bulk masses greater than ... kg/...lbs at temperatures not exceeding ... °C/...°F.',
        'P420': 'Store separately.',
        'P422': '(Obsolete) Store contents under ...',
        'P402+P404': 'Store in a dry place. Store in a closed container.',
        'P403+P233': 'Store in a well-ventilated place. Keep container tightly closed.',
        'P403+P235': 'Store in a well-ventilated place. Keep cool.',
        'P410+P403': 'Protect from sunlight. Store in a well-ventilated place.',
        'P410+P412': 'Protect from sunlight. Do not expose to temperatures exceeding 50 °C/122°F.',
        'P411+P235': '(Obsolete) Store at temperatures not exceeding ... °C/...°F. Keep cool.',
        'P501': 'Dispose of contents/container to ...',
        'P502': 'Refer to manufacturer or supplier for information on recovery or recycling',
        'P503': 'Refer to manufacturer/supplier... for information on disposal/recovery/recycling.',
    }
    ret = [mapping[_] for _ in s.split()]
    return ret


# cas_to_cid()
# get_common_names()
# find_literature()
# sanitize_synonyms()
# sfind_lit2()
# process_manual_search()
# parse_pubmed()
# offline_search()
# search_offline_csvs()
# convert_pubmed_to_json()
# offline_json_search()
#gen_deduct_freq_analysis()
#do_pubmed_freq_analysis()
#gen_edcdb()
#most_common_words()

#find_best_synonyms()
#process_synonym_log()
#pubchem_hsdb_data_download()
#hsdb_data_download()
parse_cheminfo()

#with open('deduct_word_scores.json','r') as f:
#    all_words = json.load(f)
#with open('deduct_word_scores_final.json','r') as f:
#    final_words = json.load(f)
#diffs = dict()
#for k,w in final_words.items():
#    try:
#        if w > 10:
#            del all_words[k]
#    except:
#        pass

#for k, v in reversed(sorted(all_words.items(), key=lambda item: item[1])):
#    print(k,v)


#print(all_words)

#with open('scratch_23.txt','r') as f:
#    gathered_papers = {w.strip() for w in f.readlines()}
#from raw_data import ALL_PAPERS
#from scratch_19 import DEDUCT_FINAL_PAPERS
#papers = {p.replace('PMID:','') for p in ALL_PAPERS}
#print(len(gathered_papers))
#print(len(papers.intersection(gathered_papers))/len(papers))
#print(len(DEDUCT_FINAL_PAPERS.intersection(gathered_papers))/len(DEDUCT_FINAL_PAPERS))

#count = 0

#with open('pubmed_freq_scores.csv','r') as in_f, open('emily_papers.csv','w') as out_f:
#    reader = csv.DictReader(in_f)
#    writer = csv.DictWriter(out_f,['pmid', 'score', 'title', 'date', 'journal', 'pubtype', 'abstract', 'chemicals', 'topics',
#                   'keywords', 'meshterms'])
#    for line in reader:
#        if line['pmid'] not in papers:
#            writer.writerow(line)
#            count += 1
#            print(line)

#print(count)