import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)


import checklist

import argparse
import copy
import json
import pandas as pd


from tqdm import tqdm

from parse_string import LlamaParser
from agents import AgentEmbSearch, HuggingfaceChatbot
from utils import *

import random
import numpy as np
import torch


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')



def set_seeds(args):
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

def main(args):
    set_seeds(args)
    log(str(args)+"\n",args.log_path)
    check_list, role_kg, attribute_kg,cases = checklist.prepare(arg_event_path = args.events_path)


    kb = read_kb(args.kb_path)
    args.kb = kb
    #events = events[:5]
    ### if use api, replace chatbot with empty string
    if args.api_name:
        chatbot = ''
    else:    
        chatbot = HuggingfaceChatbot(args.model)
    agents = AgentEmbSearch(chatbot, args, LlamaParser())
    predictions = []
    results = []

    ### new appened for continuing eval from errors
    ids,accs = parse_log(args.log_path)
    last_id = ids[-1] if ids else -1
    if(last_id != -1):
        acc = accs[-1]
        correct = round(acc*(last_id+1))
        results = [0] * last_id
        results.append(correct)
        print(f'last_id: {last_id} with acc {acc}, total correct: {correct}')
    else:
        print('start from index 0')


    for i,case in enumerate(cases):
        # if i < 110: continue
        if i <= last_id:
            continue
        cur_case = checklist.emb_search(check_list,role_kg, case)
        decision = agents.action(cur_case, use_gt = args.use_gt)
        decision["id"] = i
        if not "decision" in  decision:
            results.append(0)
            continue
        log(str(decision)+"\n", args.log_path)
        results.append(decision["decision"] in cur_case['norm_type'])
        print(sum(results) / len(results))
        log(str(sum(results) / len(results)) + "\n", args.log_path)
        print(f'{i} / {len(cases)} done.')
    acc = (sum(results) / len(results))
    log(str(f"accuracy:{acc}"), args.log_path)



def parse_log(log_path):
    import ast
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
    except:
        return []
    
    results = []
    acc = []
    for line in lines:
        if "{" == line[0]:
            cur_dict = ast.literal_eval(line.strip())
            id = cur_dict["id"]
            results.append(id)
        if line.startswith("0."):
            acc.append(float(line.strip()))
    return results, acc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct")

    parser.add_argument("--events_path", type=str, default="chatgpt_answer_case/real.csv")
    parser.add_argument("--kb_path", type=str, default="KB_annotated.json")
    parser.add_argument("--log_path", type=str, default='emb_search_temp.txt')


    parser.add_argument("--law_template", type=str, default="prompts/cot-knowledge-lookup-prompt.txt")
    parser.add_argument("--law_filter_template", type=str, default="prompts/3-beam-law-filter-1by1.txt")
    parser.add_argument("--law_judge_template", type=str, default="prompts/3-cot-judge-regulation-prompt.txt")
    parser.add_argument("--decision_making_template", type=str, default="prompts/4-cot-decision-making-merge.txt")


    parser.add_argument("--lawyer_tokens", type=int, default=512)
    parser.add_argument("--law_filter_tokens", type=int, default=512)
    parser.add_argument("--decision_tokens", type=int, default=512)
    parser.add_argument("--law_judge_tokens", type=int, default=512)

    parser.add_argument("--law_generation_round", type=int, default=3)
    parser.add_argument("--law_filtering_round", type=int, default=3)
    parser.add_argument("--generation_round", type=int, default=10)
    parser.add_argument("--max_law_items", type=int, default=3)
    parser.add_argument("--look_up_items", type=int, default=3)

    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument("--use_gt", type=str2bool,default=True,
                        help="Use ground truth references for testing or not.")
    parser.add_argument("--parse_1by1", type=str2bool,default=True,
                        help="filter regulations one by one or filter all of them together.")
    
    ## newly appended
    parser.add_argument("--api_name", type=str, default='Qwen/Qwen2-7B-Instruct')
    # api_bearer_token
    parser.add_argument("--api_bearer_token", type=str, default='')


    args = parser.parse_args()
    ###lhr new add for debug
    #args.log_path = os.path.join(BASE_DIR,'logs', args.log_path)
    args.events_path = os.path.join(BASE_DIR, args.events_path)
    args.kb_path = os.path.join(BASE_DIR, args.kb_path)
    args.law_template = os.path.join(BASE_DIR, args.law_template)
    args.law_filter_template = os.path.join(BASE_DIR, args.law_filter_template)
    args.law_judge_template = os.path.join(BASE_DIR, args.law_judge_template)
    args.decision_making_template = os.path.join(BASE_DIR, args.decision_making_template)

    main(args)