import json
import os
import sys
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(BASE_DIR)
import checklist.path_config as path_config


import pickle
import torch
import checklist.parse_case as parse_case
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from checklist.wordnet_align import build_role_network


import networkx as nx
import re
from tqdm import tqdm
#from chatgpt_extract import *

def read_graphml(filename):
    '''
    Read graph from file of graphml format
    '''
    G = nx.read_graphml(filename)
    return G





def find_ancestors(G, actor_role,role_list):
    '''
    G: networkx graph role_kg.G
    role: the target role for dfs
    '''
    ancestors = set()
    for role in actor_role:
        ### make sure role is in G
        if role not in G:
            continue
        find_ancestors_helper(G, role, ancestors)
    ### align ancestors with the role list
    role_set =set(role_list)
    ancestors = ancestors.intersection(role_set)
    ancestors.update(actor_role)
    ### hard code to add anyone
    if('person' in ancestors):
        ancestors.add('anyone')
    #ancestors = list(ancestors)
    return list(ancestors)

def find_ancestors_helper(G, role,ancestors):
    '''
    G: networkx graph role_kg.G
    role: the target role for dfs
    ancestors: the set to store the ancestors
    '''
    if role == 'person':
        return 
    for node in G[role]:
        if(G[role][node]["relation"] == 'is subsumed by'):
            if node not in ancestors:
                ancestors.add(node)
                find_ancestors_helper(G, node, ancestors)

    

class Checklist:
    def __init__(self,G, KB,
                 emb_model = 'all-mpnet-base-v2',
                 device = 'cuda'
                 ):
        '''
        G: networkx graph converted from HTML files
        KB: dict, the parsed data from the legislation
        '''
        assert isinstance(G, nx.DiGraph), 'G should be a networkx digraph'
        assert isinstance(KB, dict), 'KB should be a dict'
        self.G = G
        self.KB = KB
        self.emb_model = SentenceTransformer(emb_model, device=device)


    def subsume_dfs(self, node_index, verbose = False):
        '''
        Get the leaf nodes of the subsume tree of the given node
        '''
        G = self.G
        
        leaf_list = []
        
        self.subsume_dfs_helper(G, node_index, leaf_list, verbose = verbose, count = 0)
        self.leaf_list = leaf_list
        return leaf_list
    
    def get_roles(self):
        '''
        get the sender receiver and subject role list
        '''
        role_set = set()
        for node in self.KB:
            temp_dict = self.KB[node]
            if(temp_dict["norm_type"] in ['positive_norm', 'negative_norm']):
                sender = temp_dict['sender']
                receiver = temp_dict['recipient']
                subject = temp_dict['subject']
                role_set.update(sender)
                role_set.update(receiver)
                role_set.update(subject)
        self.role_list = list(role_set)

    def get_role_embeddings(self):
        assert hasattr(self, 'role_list'), 'role_list is not found, please run get_roles() first'
        role_list = self.role_list
        role_embeddings = self.emb_model.encode(role_list,convert_to_tensor=True)
        self.role_embeddings = role_embeddings


    def associate_role_KG(self,role_G):
        '''
        find ancestors for the given role list based on role_G
        '''

    def semantic_search(self, query, top_k = 3, verbose = False):
        '''
        query: str, the query sentence
        top_k: int, the number of top k results
        '''
        assert hasattr(self, 'role_embeddings'), 'role_embeddings is not found, please run get_role_embeddings() first'
        query_embedding = self.emb_model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, self.role_embeddings)[0]
        values, indices = torch.topk(cos_scores, top_k)
        ret = []
        for i in indices:
            if verbose:
                print(f"{query} \t {self.role_list[i]} \t Score: {cos_scores[i]}")
            #ret.append((checklist.role_list[i], cos_scores[i]))
            ret.append(self.role_list[i])
        '''
        hard coding part
        '''
        ### re-align the list (patient <-> individual)
        if 'patient' in ret and 'individual' not in ret:
            ret.append('individual')
        if 'individual' in ret and 'patient' not in ret:
            ret.append('patient')
        
        

        return ret
    
    def find_rules(self,sender_list,subject_list,receiver_list):
        '''
        Find associated rules given the list of sender, subject and receiver
        '''
        rules = []
        for node in self.KB:
            temp_dict = self.KB[node]
            if(temp_dict["norm_type"] in ['positive_norm', 'negative_norm']):
                senders = temp_dict['sender']
                receivers = temp_dict['recipient']
                subjects = temp_dict['subject']
                count = 0
                if any(element in sender_list for element in senders):
                    count += 1
                if any(element in receiver_list for element in receivers):
                    count += 1
                if any(element in subject_list for element in subjects):
                    count += 1
                if count == 3:
                    rules.append(node)

        return rules

    def subsume_dfs_helper(self, G, node_index, leaf_list, verbose, count = 0):
        space = '    ' * count
        subsume_count = 0
        for node in G[node_index]:
            #refer
            if G[node_index][node]['relation'] == 'refer':
                if verbose:
                    print(space,end='')
                    print(f'{node_index} -> {G[node_index][node]["relation"]}->{node}')
            if G[node_index][node]['relation'] == 'subsume':
                subsume_count += 1
                if verbose:
                    print(space,end='')
                    print(f'{node_index} -> {G[node_index][node]["relation"]}->{node}')
                count += 1
                self.subsume_dfs_helper(G, node, leaf_list, verbose, count=count)
                count -= 1
        if subsume_count == 0:
            if verbose:
                print(space,end='----')
                print(f'{node_index} is leaf')
            leaf_list.append(node_index)


class RoleKG:
    def __init__(self):
        self.G = self.get_role_graph()

    
    def get_role_graph(self, type = 'default'):
        '''
        default: the default role graph (naive version extracted from chatgpt in 04/2023)
        '''
        if type == 'default':
            G = build_role_network()
        else:
            raise NotImplementedError
        return G

class AttributeKG:
    def __init__(self,data_dir):
        self.data_dir = data_dir
        self.get_attribute_graph()
        pass

    def get_attribute_graph(self, type = 'default'):
        '''
        default: the default attribute graph (ontologies extracted from OPPO and DPV)
        '''
        if type == 'default':
            path = os.path.join(self.data_dir,'attribute_graph.pickle')
            with open(path, 'rb') as f:
                self.G = pickle.load(f)
        else:
            raise NotImplementedError
        #return self.G

def format_rules(rules, KB):
    '''
    rules: list of rule ids
    KB: checklist KB
    Find common root for the rules to avoid redundancy
    '''
    rule_dict = {}
    for rule_id in rules:
        if rule_id not in KB:
            print(f'{rule_id} not found in KB')
            continue
        rule = KB[rule_id]
        cut_off_index = rule_id.rfind('(')
        ## get root id
        if cut_off_index != -1:
            root_id = rule_id[:cut_off_index]
            sep = rule_id[cut_off_index:]
        else:
            print(f'cannot find the root id for {rule_id}')
            raise NotImplementedError
            root_id = rule_id
            sep = ''
        root_text_split = rule['text'].rsplit(sep,maxsplit=1)
        #assert len(root_text_split) == 2, 'root text should be 2 sentences'
        if(len(root_text_split) != 2):
            print(f'boundary case {rule_id} cannot split on {sep}')
            root_text_split = rule['text'].rsplit('\n',maxsplit=1)
        assert len(root_text_split) == 2, 'root text should be 2 sentences'
        if root_id not in rule_dict:
            
            rule_dict[root_id] = {
                'root_text': root_text_split[0],
                'sub_rules': [sep],
                'sub_text': [root_text_split[1]]
            }
        else:
            if(sep not in rule_dict[root_id]['sub_rules']):
                rule_dict[root_id]['sub_rules'].append(sep)
                rule_dict[root_id]['sub_text'].append(root_text_split[1])

    return rule_dict

def evaluate_on_semantic_search(checklist,
                                role_kg,
                                data_type = 'real',
                                top_k = 3,
                                verbose = False):
    '''
    evaluation using semantic search (embedding similarity based retrival)
    '''
    ### return the ids of privacy rules
    def semantic_search(checklist,case):
        sender, subject, recipient = case['sender'], case['subject'], case['recipient'] ### 3 role lists, ### retrival ancestors from the role_kg

        sender_list = checklist.semantic_search(sender, top_k = top_k, verbose = verbose)
        sender_list = find_ancestors(role_kg.G, sender_list, checklist.role_list)
        subject_list = checklist.semantic_search(subject, top_k = top_k, verbose = verbose)
        subject_list = find_ancestors(role_kg.G, subject_list, checklist.role_list)
        receiver_list = checklist.semantic_search(recipient, top_k = top_k, verbose = verbose)
        receiver_list = find_ancestors(role_kg.G, receiver_list, checklist.role_list)
        ### re-align the list (patient <-> individual)

        rules = checklist.find_rules(sender_list, subject_list, receiver_list)
        return rules
    
    ### get the ids from the parsed gt, traverse the parsed gt with checklist to reach leaves
    def gt_search(checklist,case):
        #sender, subject, recipient = case['sender'], case['subject'], case['recipient']
        refer_ids = case['refer_ids']
        rules = []
        for refer_id in refer_ids:
            try:
                rules.extend(checklist.subsume_dfs(refer_id))
            except:
                print(f'Error: {refer_id}')
                
        return rules


    cases = parse_case.get_cases(data_type)
    #sender, subject, receiver = cases[]
    ret = []
    for case in cases:
        data_dict = {}
        semantic_rules = semantic_search(checklist,case)
        gt_rules = gt_search(checklist,case)
        semantic_rule_dict = format_rules(semantic_rules, checklist.KB)
        gt_rule_dict = format_rules(gt_rules, checklist.KB)
        case['semantic_rules'] = semantic_rule_dict
        case['gt_rules'] = gt_rule_dict

    ## save to json
    save_dir = os.path.join(data_dir,'..', 'cases')
    with open(os.path.join(save_dir, f'{data_type}.json'), 'w') as f:
        json.dump(cases, f)

    ### save to pandas csv
    df = pd.DataFrame(cases)
    df.to_csv(os.path.join(save_dir, f'{data_type}.csv'), index=False)

    print('done')
    return cases






def emb_search(checklist,
                role_kg,
                case,
                data_type = 'real',
                top_k = 3,
                verbose = False):
    '''
    evaluation using semantic search (embedding similarity based retrival)
    '''
    ### return the ids of privacy rules
    def semantic_search(checklist,case):
        sender, subject, recipient = case['sender'], case['subject'], case['recipient']
        print(f'sender: {sender}, subject: {subject}, recipient: {recipient}') 
        sender = str(sender)
        subject = str(subject)
        recipient = str(recipient)
        ### 3 role lists, ### retrival ancestors from the role_kg
        sender_list = checklist.semantic_search(sender, top_k = top_k, verbose = verbose)
        sender_list = find_ancestors(role_kg.G, sender_list, checklist.role_list)
        subject_list = checklist.semantic_search(subject, top_k = top_k, verbose = verbose)
        subject_list = find_ancestors(role_kg.G, subject_list, checklist.role_list)
        receiver_list = checklist.semantic_search(recipient, top_k = top_k, verbose = verbose)
        receiver_list = find_ancestors(role_kg.G, receiver_list, checklist.role_list)
        ### re-align the list (patient <-> individual)

        rules = checklist.find_rules(sender_list, subject_list, receiver_list)
        return rules
    
    ### get the ids from the parsed gt, traverse the parsed gt with checklist to reach leaves
    def gt_search(checklist,case):
        #sender, subject, recipient = case['sender'], case['subject'], case['recipient']
        refer_ids = case['refer_ids']
        rules = []
        for refer_id in refer_ids:
            try:
                rules.extend(checklist.subsume_dfs(refer_id))
            except:
                print(f'Error: {refer_id}')
                
        return rules

    semantic_rules = semantic_search(checklist,case)
    gt_rules = gt_search(checklist,case)
    semantic_rule_dict = format_rules(semantic_rules, checklist.KB)
    gt_rule_dict = format_rules(gt_rules, checklist.KB)
    ### dict with ids as key and text as value
    case['semantic_rules'] = semantic_rule_dict
    case['gt_rules'] = gt_rule_dict

    return case





def prepare(arg_event_path = ''):
    data_dir = path_config.data_dir
    graph_path = path_config.graph_path
    G = read_graphml(graph_path)
    parse_file_name = path_config.KB_path
    with open(parse_file_name, 'r') as f:
            parse_data = json.load(f)

    node_index = path_config.node_index
    KB = parse_data

    checklist = Checklist(G, KB)
    checklist.subsume_dfs(node_index, verbose = False)
    checklist.get_roles()
    checklist.get_role_embeddings()
    role_kg = RoleKG()
    attribute_kg = AttributeKG(data_dir)
    if arg_event_path:
        if('eval_generate' in arg_event_path):
            print(f'load generated cases')
            cases = parse_case.get_cases(type = 'generate')
        elif('eval_real' in arg_event_path):
            print(f'load real cases')
            cases = parse_case.get_cases(type = 'real')
        else:
            raise NotImplementedError
    else:
        print(f'load cases from {path_config.data_type}')
        cases = parse_case.get_cases(type = path_config.data_type)
    return checklist, role_kg, attribute_kg,cases 

if __name__ == "__main__":



    data_dir = path_config.data_dir
    graph_path = path_config.graph_path
    G = read_graphml(graph_path)
    parse_file_name = path_config.KB_path
    with open(parse_file_name, 'r') as f:
            parse_data = json.load(f)

    node_index = path_config.node_index
    KB = parse_data

    checklist = Checklist(G, KB)
    checklist.subsume_dfs(node_index, verbose = False)
    checklist.get_roles()
    checklist.get_role_embeddings()
    role_kg = RoleKG()
    attribute_kg = AttributeKG(data_dir)
    print('end')
    cases = evaluate_on_semantic_search(checklist,role_kg, data_type = path_config.data_type)