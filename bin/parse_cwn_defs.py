import re
import json
import socket
from pathlib import Path
from CwnGraph import CwnBase
from tqdm.auto import tqdm


def build_xml(content):
    request_xml = """
<?xml version="1.0" ?>
<wordsegmentation version="0.1">
<option showcategory="1" />
<authentication username="seantyh" password="33669904" />
<text>{}</text>
</wordsegmentation>
    """
    return request_xml.format(content)

def parse_def(sock, text):
    try:
        request_xml = build_xml(text)
        sock.sendall(request_xml.encode("big5"))
    
        buf_size = 32
        data = b""
        while True:
            received = sock.recv(buf_size)                
            data += received    
            if data.endswith(b"\r\n"):
                break

    except Exception as ex:
        print("ERROR: ", ex)
        data = b""
    except UnicodeEncodeError as ex:
        print(ex)
        print(request_xml)
        data = b""
        
    xml = data.decode("big5")
    sentences = re.findall("<sentence>(.*?)</sentence>", xml)
    return sentences

def split_batch(batch, sep=None):
    if sep is None:
        sep = "S(NP(Head:N:你)|Head:Vi:好)#。(PERIODCATEGORY)"
    groups = []
    buf = []
    for x in batch:
        if sep in x:
            groups.append(buf)
            buf = []
        else:
            buf.append(x)
    if buf:
        groups.append(buf)
    return groups

if __name__ == "__main__":
    ## preparing definitions
    cwn = CwnBase()
    senses = cwn.get_all_senses()
    all_defs = list(set(x.definition for x in senses if x.definition))
    
    ## loading cache
    cache_path = Path("../data/cwn_def_ckip_parsed.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        fin = cache_path.open()
        cwn_def_ckip_parsed = json.load(fin)    
        print("load cache from ", cache_path)
        fin.close()
    else:
        cwn_def_ckip_parsed = {}
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        server_address = ('140.109.19.112', 8000)
        print('connecting to %s port %s' % server_address)
        sock.connect(server_address)
                
        n_unsaved = 0
        batch_size = 5
        batch_defs = []
        
        for def_i, def_x in tqdm(enumerate(all_defs), total=len(all_defs)):            
            if def_x not in cwn_def_ckip_parsed:
                batch_defs.append(def_x)                
            
            if len(batch_defs) == batch_size \
                or def_i == len(all_defs)-1:
                
                batch_input = "\r\n你好。\r\n".join(batch_defs)
                batch_parsed = parse_def(sock, batch_input)                
                
                if not batch_parsed:
                    continue
                
                batch_results = split_batch(batch_parsed)
                assert len(batch_defs) == len(batch_results)
                for def_x, res_x in zip(batch_defs, batch_results):
                    cwn_def_ckip_parsed[def_x] = res_x
                batch_defs = []
                n_unsaved += len(batch_results)

            if n_unsaved > 10:
                print("Saving progress to ", cache_path)
                fout = cache_path.open("w", encoding="UTF-8")
                json.dump(cwn_def_ckip_parsed, fout, 
                          indent=2, ensure_ascii=False)
                n_unsaved = 0
                fout.close()
                break