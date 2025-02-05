import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"




import argparse
import copy
import json
import pandas as pd
import sys

from tqdm import tqdm

from parse_string import LlamaParser
from agents import AgentsIdSearch , HuggingfaceChatbot
from utils import *

import random
import numpy as np
import torch

def set_seeds(args):
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

def main(args):
    set_seeds(args)
    log(str(args),args.log_path)
    events = read_events(args.events_path)
    kb = read_kb(args.kb_path)
    args.kb = kb
    #events = events[:5]
    ### if use api, replace chatbot with empty string
    if args.api_name:
        chatbot = ''
    else:    
        chatbot = HuggingfaceChatbot(args.model)
    agents = AgentsIdSearch(chatbot, args, LlamaParser())
    predictions = []
    results = []
    ### new appened for continuing eval from errors
    #ids,accs = parse_log(args.log_path)
    #last_id = ids[-1] if ids else -1
    last_id = -1
    if(last_id != -1):
        acc = accs[-1]
        correct = round(acc*(last_id+1))
        results = [0] * last_id
        results.append(correct)
        print(f'last_id: {last_id} with acc {acc}, total correct: {correct}')
    else:
        print('start from index 0')
    for i in tqdm(range(len(events))):
        # if i < 110: continue
        if i <= last_id:
            continue
        event = events.loc[i]
        decision = agents.action(event.context)
        decision["id"] = i
        if not "decision" in  decision:
            results.append(0)
            continue
        log(str(decision)+"\n", args.log_path)
        results.append(decision["decision"] in event.norm_type)
        print(sum(results) / len(results))
        log(str(sum(results) / len(results))+"\n",args.log_path)
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
    parser.add_argument("--log_path", type=str, default="logs/log.txt")

    parser.add_argument("--law_template", type=str, default="prompts/2-cot-law-prompt.txt")
    parser.add_argument("--law_filter_template", type=str, default="prompts/3-beam-law-filter-prompt.txt")
    parser.add_argument("--decision_making_template", type=str, default="prompts/4-cot-decision-making.txt")

    parser.add_argument("--lawyer_tokens", type=int, default=512)
    parser.add_argument("--law_filter_tokens", type=int, default=512)
    parser.add_argument("--decision_tokens", type=int, default=512)



    parser.add_argument("--law_filtering_round", type=int, default=3)
    parser.add_argument("--law_generation_round", type=int, default=3)
    parser.add_argument("--max_law_items", type=int, default=4)
    parser.add_argument("--generation_round", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--api_name", type=str, default='')
    # api_bearer_token
    parser.add_argument("--api_bearer_token", type=str, default='')


    args = parser.parse_args()

    args.events_path = os.path.join(BASE_DIR, args.events_path)
    args.kb_path = os.path.join(BASE_DIR, args.kb_path)
    args.log_path = os.path.join(BASE_DIR, args.log_path)
    args.law_template = os.path.join(BASE_DIR, args.law_template)
    args.law_filter_template = os.path.join(BASE_DIR, args.law_filter_template)
    args.decision_making_template = os.path.join(BASE_DIR, args.decision_making_template)


    main(args)
