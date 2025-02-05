import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)
data_dir = os.path.join(BASE_DIR, 'data')

domain = 'HIPAA'
node_index = '164.502'
data_type = 'real'  ### two data types: 'real' and 'generate'

data_dir = os.path.join(data_dir, domain)
generate_case_path = os.path.join(data_dir, 'eval_generate.csv')
real_case_path = os.path.join(data_dir, 'eval_real.csv')
graph_path = os.path.join(data_dir, 'HIPAA.graphml')
KB_path = os.path.join(data_dir, 'KB_annotated.json')
entity_csv_path = os.path.join(data_dir, 'entities.csv')
relation_csv_path = os.path.join(data_dir, 'relations.csv')