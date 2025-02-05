import argparse
import copy
import json
import pandas as pd
import sys

from tqdm import tqdm

from parse_string import LlamaParser
from agents import AgentTrieSearch, HuggingfaceChatbot
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
    chatbot = HuggingfaceChatbot(args.model)
    agents = AgentTrieSearch(chatbot, args, LlamaParser())
    predictions = []
    results = []
    for i in tqdm(range(len(events))):
        # if i < 107: continue
        event = events.loc[i]
        decision = agents.action(event.context)
        if not "decision" in  decision:
            results.append(0)
            continue
        log(str(decision)+"\n", args.log_path)
        results.append(decision["decision"] in event.norm_type)
        print(sum(results) / len(results))
    acc = (sum(results) / len(results))
    log(str(f"accuracy:{acc}"), args.log_path)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="/data/zzh/cyl/privacy/llama3-8b-instruct/")

    parser.add_argument("--events_path", type=str, default="chatgpt_answer_case/real.csv")
    parser.add_argument("--kb_path", type=str, default="KB_annotated.json")
    parser.add_argument("--log_path", type=str, default="logs/log.txt")

    parser.add_argument("--law_template", type=str, default="prompts/2-beam-law-prompt.txt")
    parser.add_argument("--law_filter_template", type=str, default="prompts/3-beam-law-filter-prompt.txt")
    parser.add_argument("--decision_making_template", type=str, default="prompts/4-decision-making.txt")


    parser.add_argument("--lawyer_tokens", type=int, default=512)
    parser.add_argument("--law_filter_tokens", type=int, default=512)
    parser.add_argument("--decision_tokens", type=int, default=512)


    parser.add_argument("--law_generation_round", type=int, default=3)
    parser.add_argument("--law_filtering_round", type=int, default=3)
    parser.add_argument("--generation_round", type=int, default=8)
    parser.add_argument("--max_law_items", type=int, default=4)
    parser.add_argument("--max_depth", type=int, default=4)

    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args)
