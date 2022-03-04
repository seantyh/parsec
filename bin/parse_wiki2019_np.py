import sys
sys.path.append("../src")
import os
import re
import json
import zipfile
from itertools import islice
from collections import Counter
from tqdm.auto import tqdm
import pandas as pd
import opencc
from stanza.server import CoreNLPClient
from stanford_utils import *

import logging
logging.getLogger().setLevel("WARNING")
os.environ["CORENLP_HOME"] = os.path.expanduser("~/etc/stanford-corenlp-4.4.0")

SAMPLE_EVERY_N = 25

def iterate_wiki_file(wiki_zip_path):
    fin = open(wiki_zip_path, "rb")
    zipf = zipfile.ZipFile(fin)
    infolist = sorted(zipf.infolist(), key=lambda x: x.filename)
    counter = -1
    for info_x in filter(lambda x: not x.is_dir(), infolist):        
        counter += 1
        if counter % SAMPLE_EVERY_N > 0:            
            continue
        with zipf.open(info_x) as fwiki:
            text = fwiki.read().decode()
            data = []
            for ln in text.split("\n"):
                ln = ln.strip()
                if not ln: continue
                try:
                    data.append(json.loads(ln))                
                except Exception as ex:
                    print(ex)
        yield(info_x, data)
    fin.close()
    
if __name__ == "__main__":
    
    t2s = opencc.OpenCC('t2s.json')
    np_freqs = Counter()
    n_charac = 0
    n_entry = 0
    
    with CoreNLPClient(properties="chinese",
            annotators=['tokenize','ssplit','pos','parse'],
            timeout=30000,
            memory='6G', be_quiet=True) as client:
        for info, data in iterate_wiki_file("../data/wiki_zh_2019.zip"):            
            for entry_x in tqdm(data, desc=info.filename):                
                if "text" not in entry_x: continue
                try:
                    text_simp = t2s.convert(entry_x["text"])
                    n_charac += len(text_simp)
                    n_entry += 1
                    ann = client.annotate(text_simp)
                    
                    for sent_x in ann.sentence:
                        npc_nodes = get_nodes(sent_x.parseTree, is_np_compound)
                        if not npc_nodes: continue
                        np_compounds = [flatten_compound(np_x)
                                        for np_x in npc_nodes]                
                        np_freqs.update([(*x[0], *x[1]) for x in np_compounds])
                except Exception as ex:
                    logging.error("ERROR: " + str(ex))            
    
    with open("../data/wiki2019_compounds.csv", "w", encoding="UTF-8") as fout:
        fout.write("idx,np,nptype,w1,w2,p1,p2,freq\n")
        for np_i, (np_item, np_freq) in enumerate(np_freqs.most_common()):            
            w1, w2, p1, p2 = np_item            
            nptype = f"{len(w1)}{len(w2)}"
            fout.write(f'{np_i+1},"{w1+w2}",{nptype},')
            fout.write(f'"{w1}","{w2}","{p1}","{p2}",{np_freq}\n')
    
    npc = pd.read_csv("../data/wiki2019_compounds.csv", index_col=0)
    compounds_nn2 = npc.loc[(npc.nptype==22) & ((npc.p1=="NN") & (npc.p2=="NN")), :].reset_index(drop=True)
    compounds_nn2.index.name = "idx"
    compounds_nn2.to_csv("../data/wiki2019_compounds_nn2.csv")
            
    print("n_entry: ", n_entry)
    print("n_charac: ", n_charac)
        
    with open("../data/wiki2019_compounds.log", "w") as fout:
        fout.write(f"sample_every_n: {SAMPLE_EVERY_N}\n")
        fout.write(f"n_entry: {n_entry}\n")
        fout.write(f"n_charac: {n_charac}\n")
            