import re

import pandas as pd
import json
import os

def list_intersection(candidates, vote_number=-1):
    if vote_number == -1:
        ### LHR modified
        vote_number = len(candidates) // 2 + 1
    counter = {}
    for candidate in candidates:
        for c in candidate:
            if c not in counter:
                counter[c] = 0
            counter[c] += 1
    temp = []
    for key, value in counter.items():
        if value >= vote_number:
            temp.append([key, value])
    ret = []
    ret = sorted(temp, key=lambda x: x[1], reverse=True)
    ret = [x[0] for x in ret]
    return ret

def read_events(path):
#real.csv
    events = pd.read_csv(path)
    return events

def read_kb(path):
    with open(path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    return kb

def log(message, path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(message+"\n")
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write(message+"\n")




class Trie:
    def __init__(self, id, content):
        self.id = id
        self.content = content
        self.sons = {}
        self.pattern = r"[0-9]+\.[0-9]+|\([0-9A-Za-zivx]+\)"
    def add_sons(self, contents):

        if isinstance(contents, str):
            contents = contents.strip().split("\n")
        cur_trie = self
        for content in contents:
            if not content: continue
            search = re.search(self.pattern, content)
            if search is not None:
                start, end = search.span()
                id = content[start:end]
                if id in cur_trie.sons:
                    cur_trie = cur_trie.sons[id]
                else:
                    cur_trie.sons[id] = Trie(id, content)
                    cur_trie = cur_trie.sons[id]
            else:
                break

    def search_content(self, id_seq):
        ret_content = []
        cur_trie = self
        while True:
            search = re.search(self.pattern, id_seq)
            if search is None:
                break
            start, end = search.span()
            id = id_seq[start:end]
            if id in cur_trie.sons:
                cur_trie = cur_trie.sons[id]
                ret_content.append(cur_trie.content)
                id_seq = id_seq[end:]
            else:
                break
        return ret_content

    def search_sons(self, id_seq):
        # ret_content = []
        cur_trie = self
        while True:
            search = re.search(self.pattern, id_seq)
            if search is None:
                break
            start, end = search.span()
            id = id_seq[start:end]
            if id in cur_trie.sons:
                cur_trie = cur_trie.sons[id]
                # ret_content.append(cur_trie.content)
                id_seq = id_seq[end:]
            else:
                break
        return cur_trie.sons



