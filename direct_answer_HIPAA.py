import argparse
import copy
import json
import pandas as pd
import sys

from tqdm import tqdm

from parse_string import LlamaParser
from agents import AgentAction, HuggingfaceChatbot
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

    #events = events[:5]
    ### if use api, replace chatbot with empty string
    if args.api_name:
        chatbot = ''
    else:    
        chatbot = HuggingfaceChatbot(args.model)
    agents = AgentAction(chatbot, args.prompt_template, LlamaParser().parse_decision,
                         max_new_tokens=args.max_new_tokens , 
                         api_name= args.api_name)
    predictions = []
    results = []
    for i in tqdm(range(len(events))):
        event = events.loc[i]
        decision = {}
        for _ in range(args.generation_round):
            try:
                decision = agents.complete(event=event.context)

                log(str(decision)+"\n", args.log_path)
                results.append(decision["decision"] in event.norm_type)
                # print(results[-1])
                print(sum(results) / len(results))
                if decision: break

            except: continue
        if not decision: results.append(0)

    acc = (sum(results) / len(results))
    print(acc)
    log(str(f"accuracy:{acc}"), args.log_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str)

    parser.add_argument("--events_path", type=str, default="chatgpt_answer_case/real.csv")
    parser.add_argument("--kb_path", type=str, default="KB_annotated.json")
    parser.add_argument("--log_path", type=str, default="logs/log.txt")

    parser.add_argument("--prompt_template", type=str, default="prompts/direct_answer_prompt.txt")
    parser.add_argument("--max_new_tokens", type=int, default=1024)

    parser.add_argument("--generation_round", type=int, default=10)
    parser.add_argument("--max_law_items", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--api_name", type=str, default='')
    args = parser.parse_args()
    main(args)
