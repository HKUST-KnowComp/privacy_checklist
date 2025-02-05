'''
This py file uses WordNet to align entities with 'person.n.01' synset for role KG building
This file further processes the collected csv data and use wordnet to get hierarchy for people
Note that normalization/alignment/Lemmatizer is done here
1): add more person entities according to wordnet
2): add more subsume relation according to wordnet (hypernyms)
3): Build one role KGs to represent the context
'''
import pandas as pd
import nltk
#nltk.download('omw-1.4')
#nltk.download('wordnet')
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk import WordNetLemmatizer
from nltk.corpus import wordnet as wn
import argparse
import checklist.path_config  as path_config
#import path_config
### debug 
import sys
import os
import networkx as nx
#sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
#sys.path.append(os.getcwd())

def read_csv(path):
    """
    Read csv file
    :return: dataframe
    """
    abs_path = os.path.dirname(__file__)
    filename = os.path.join(abs_path, path)
    df = pd.read_csv(filename, encoding="utf-8-sig")
    return df

def clean_text(text):
    """
    This function takes as input a text on which several 
    NLTK algorithms will be applied in order to preprocess it
    return processed texts
    """
    if not isinstance(text, str):
        print('==='*30) 
        print(f'non-string content found: {type(text)}: {text}') 
        text = str(text)
    text = text.replace('/',' or ')
    ### print(f'text: {text}') 
    tokens = word_tokenize(text)
    ### print(f'after tokenization: {tokens}') 
    # Remove the punctuations
    tokens = [word for word in tokens if word.isalpha()]
    ### print(f'after Remove the punctuations: {tokens}') 
    # Lower the tokens
    tokens = [word.lower() for word in tokens]
    ### print(f'after Lower the tokens: {tokens}') 
    # Remove stopword
    #tokens = [word for word in tokens if not word in stopwords.words("english")]
    # Lemmatize
    lemma = WordNetLemmatizer()
    tokens = [lemma.lemmatize(word, pos = "v") for word in tokens]
    tokens = [lemma.lemmatize(word, pos = "n") for word in tokens]
    return ' '.join(tokens)

def remove_stopword(text):
    """
    This function takes as input a text on which several 
    NLTK algorithms will be applied in order to preprocess it
    """
    tokens = word_tokenize(text)
    # Remove stopword
    tokens = [word for word in tokens if not word in stopwords.words("english")]
    return ' '.join(tokens)

def create_subsume_relation_from_wordnet(paths_to_person):
    """
    create subsume relation between entities
    also replace '_' with space ' ' for wordnet entities
    list of format: h,r,t,count,source
    """
    subsume_list = []
    for path in paths_to_person:
        for i in range(len(path)-1):
            head = path[i].replace('_',' ')
            tail = path[i+1].replace('_',' ')
            subsume_list.append( [head,'subsume',tail,1,'wordnet'] )
    return subsume_list

def wordnet_align_person(entity):
    """
    This function takes head or tail as input and align it to the wordnet
    to judge if it is a person.
    For now, i will use synset name to denote the entity (i.e. person.n.01)
    Otherwise, consider usage like this: [synset.name.split('.')[0] for synset in wn.synsets('dog') ]
    Return the list of path from person to the entity
    Also replace '_' with ' '
    if entity is not a person, return None
    """


    person = wn.synset('person.n.01')
    processed_entity = entity.strip().replace(' ','_')
    s_list = wn.synsets(processed_entity, pos=wn.NOUN)

    if(len(s_list) == 0): # empty list (cannot align with wordnet)
        return None
    paths_to_person = []
    is_person = False
    for s in s_list:
        paths = s.hypernym_paths()
        
        for path in paths:
            if(person in path):
                is_person = True
                p_index = path.index(person)
                temp_path = path[p_index:]
                ### we can inherit the whole attributes of synset via not spliting the name
                #temp_path = [s.name() for s in temp_path]
                temp_path = [s.name().split('.')[0].replace('_',' ') for s in temp_path]
                paths_to_person.append(temp_path)
        paths_to_person = remove_duplication(paths_to_person)
    if(is_person):
        return paths_to_person
    else:
        return None

def df_relation_clean(df):
    ### clean relation df
    df['h'] = df['h'].apply(clean_text)
    df['r'] = df['r'].apply(clean_text)
    df['t'] = df['t'].apply(clean_text)
    df['h'] = df['h'].apply(remove_stopword)
    df['t'] = df['t'].apply(remove_stopword)
    df['r'] = df['r'].apply(align_subsume_relation)
    return df

def df_entity_clean(df):
    ### clean entity df
    df['entity'] = df['entity'].apply(clean_text)
    df['entity'] = df['entity'].apply(remove_stopword)
    return df

def extract_subsume_relation_from_wordnet(df):
    """
    This function takes as input a dataframe and extract subsume relation from thw wordnet
    Also, duplicated relation will be removed
    """
    subsume_list = []
    # key: entity with path to person, val: path to person (list of paths)
    role_dict = {}
    for entity in df:
        paths_to_person = wordnet_align_person(entity)
        if(paths_to_person != None):
            role_dict[entity] = paths_to_person
            ### remove duplication here
            subsume_list.extend(create_subsume_relation_from_wordnet(paths_to_person))
    subsume_list = remove_duplication(subsume_list)
    return subsume_list,role_dict

def remove_duplication(subsume_list):
    subsume_tuple = [tuple(i) for i in subsume_list]
    subsume_tuple = list(set(subsume_tuple))
    subsume_list_deduplicate = [list(i) for i in subsume_tuple]
    return subsume_list_deduplicate

def extract_role_entity(relation_list):
    entities = [i[0] for i in relation_list] + [i[2] for i in relation_list]
    entities = list(set(entities))
    return entities


def align_subsume_relation(relation_text):
    keywords = ['include', 'contain', 'shall contain']
    for keyword in keywords:
            if(keyword == relation_text):
                return 'subsume'
    return relation_text
    
def align_df_with_role(df,role_list):
    """
    This function takes as input a dataframe and a list of roles
    and align the dataframe with the roles
    creating df of the list of dicts can be faster
    new entities that are not in WordNet will be captured in this way
    """
    row_list = []
    for index, row in df.iterrows():
        relation = row['r']
        if(relation == 'subsume'):
            head = row['h']
            tail = row['t']
            if(head in role_list or tail in role_list):
                row_list.append(row.to_dict())

    aligned_df = pd.DataFrame(row_list)
    return aligned_df

def add_new_path(df,role_list,role_dict):
    """
    This function takes as input a dataframe and a list of roles
    and align the dataframe with the roles
    creating df of the list of dicts can be faster
    new entities that are not in WordNet will be captured in this way
    """
    person = wn.synset('person.n.01')
    person = person.name().split('.')[0]
    new_role_dict = {}
    for index, row in df.iterrows():
        relation = row['r']
        if(relation == 'subsume'):
            head = row['h']
            tail = row['t']
            if(head in role_list and tail in role_list):
                pass
            # new tail entity found
            elif(head in role_list):
                ### create new path for tail (append tail to head paths' last element)
                path_list = role_dict[head]
                tail_path = [p+[tail] for p in path_list]
                role_dict[tail] = tail_path
                
            # new head entity found
            elif(tail in role_list):
                ### create new path for head (person->head)
                head_path = [[person,head]]
                role_dict[head] = head_path
                ### append new path for tail (person->head->tail)
                role_dict[tail].append([person,head,tail])
                #ic(role_dict[tail])


def extract_interaction_with_role(df,role_list):
    """
    This function takes as input a dataframe and a list of roles
    and extract the interaction between roles and possible attributes
    """
    row_list = []
    for index, row in df.iterrows():
        head = row['h']
        tail = row['t']
        relation = row['r']
        if(head in role_list or tail in role_list):
            if(relation != 'subsume'):
                row_list.append(row.to_dict())
    aligned_df = pd.DataFrame(row_list)
    return aligned_df


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--entity_file', type=str,  help='processed entity_file csv path',default=config.entity_csv_path)
    # parser.add_argument('--relation_file', type=str,  help='processed relation_file csv path',default=config.relation_csv_path)

    # args = parser.parse_args()

    entity_file = path_config.entity_csv_path
    relation_file = path_config.relation_csv_path
    entity_df = read_csv(entity_file)
    relation_df = read_csv(relation_file)
    ### data cleaning
    entity_df = df_entity_clean(entity_df)
    relation_df = df_relation_clean(relation_df)

    ### merge Roles from entity and triple list, x_dict: key: entity, val: path to person (list of paths)
    r_h, h_dict = extract_subsume_relation_from_wordnet(relation_df['h'])
    r_t, t_dict = extract_subsume_relation_from_wordnet(relation_df['t'])
    e_list, e_dict = extract_subsume_relation_from_wordnet(entity_df['entity'])
    r_wordnet = remove_duplication(e_list + r_h + r_t)
    role_dict = {**h_dict, **t_dict, **e_dict}

    ### complete the role_dict
    role_list = [i[0] for i in r_wordnet] + [i[2] for i in r_wordnet] ####[head,'subsume',tail,1,'wordnet']
    role_list = list(set(role_list))
    add_new_path(relation_df,role_list,role_dict)


    ## role_list
    align_df = align_df_with_role(relation_df,role_list)
    role_list += [r['h'] for i,r in align_df.iterrows()]
    role_list += [r['t'] for i,r in align_df.iterrows()]
    role_list = list(set(role_list))

    print('role_list complete')
    ### complete the role_dict


def build_role_network():
    '''
    convert relation_df and r_wordnet to a digraph
    '''
    entity_file = path_config.entity_csv_path
    relation_file = path_config.relation_csv_path
    entity_df = read_csv(entity_file)
    relation_df = read_csv(relation_file)
    ### data cleaning
    entity_df = df_entity_clean(entity_df)
    relation_df = df_relation_clean(relation_df)

    ### merge Roles from entity and triple list, x_dict: key: entity, val: path to person (list of paths)
    r_h, h_dict = extract_subsume_relation_from_wordnet(relation_df['h'])
    r_t, t_dict = extract_subsume_relation_from_wordnet(relation_df['t'])
    e_list, e_dict = extract_subsume_relation_from_wordnet(entity_df['entity'])
    r_wordnet = remove_duplication(e_list + r_h + r_t)

    G = nx.DiGraph()
    for i in r_wordnet:
        head, relation, tail, count, source = i
        if(relation == 'subsume'):
            G.add_edge(head, tail, relation=relation, source = source)
            G.add_edge(tail, head, relation='is subsumed by', source = source)

    for index, row in relation_df.iterrows():
        head = row['h']
        tail = row['t']
        relation = row['r']
        source = row['source']
        if(relation == 'subsume'):
            G.add_edge(head, tail, relation=relation, source = source)
            G.add_edge(tail, head, relation='is subsumed by', source = source)

    return G


if __name__ == '__main__':
    #main()
    G = build_role_network()
    print(f'nodes: {len(G.nodes())}')
    print(f'edges: {len(G.edges())}')