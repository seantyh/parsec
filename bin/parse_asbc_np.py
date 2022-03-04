import sys
sys.path.append("../../pyASBC/src")
sys.path.append("../src")
import os
from itertools import islice
from collections import Counter
import json
import logging

from tqdm.auto import tqdm
from stanford_utils import *
import pyASBC
import opencc
from stanza.server import CoreNLPClient

os.environ["CORENLP_HOME"] = os.path.expanduser("~/etc/stanford-corenlp-4.4.0")
logging.basicConfig()
logging.getLogger().setLevel("WARNING")

if __name__ == "__main__":
    np_compounds = []    
    t2s = opencc.OpenCC('t2s.json')
    asbc = pyASBC.Asbc5Corpus("../../pyASBC/data/")
    cat_mapper = lambda x: ''.join(t[0] for t in x)    
    
    with CoreNLPClient(properties="chinese",
            annotators=['tokenize','ssplit','pos','parse', 'depparse'],
            timeout=30000,
            memory='6G', be_quiet=True) as client:
        cat_iter = map(cat_mapper, asbc.iter_sentences())
        # cat_iter = islice(cat_iter, 0, 100)
        
        for intext in tqdm(cat_iter):
            try:
                text_simp = t2s.convert(intext)
                ann = client.annotate(text_simp)
                sent0 = ann.sentence[0]
                npc_nodes = get_nodes(sent0.parseTree, is_np_compound)
                if npc_nodes:
                    np_compounds.extend([flatten_compound(np_x)
                                         for np_x in npc_nodes])
            except Exception as ex:
                logging.error(ex)
        
    np_freqs = Counter((*x[0], *x[1]) for x in np_compounds).most_common()
    
    with open("../data/asbc_compounds.csv", "w", encoding="UTF-8") as fout:
        fout.write("idx,np,nptype,w1,w2,p1,p2,freq\n")
        for np_i, (np_item, np_freq) in enumerate(np_freqs):            
            w1, w2, p1, p2 = np_item            
            nptype = f"{len(w1)}{len(w2)}"
            fout.write(f"{np_i+1},{w1+w2},{nptype},")
            fout.write(f"{w1},{w2},{p1},{p2},{np_freq}\n")
                    
