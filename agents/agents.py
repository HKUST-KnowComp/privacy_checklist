import copy
import sys
import os
#sys.path.append("../")
from agents.bm25 import BM25
from utils import Trie, list_intersection
from config import API_key
import json
import requests

def respond_via_api(message, api_name, max_new_tokens=128, api_bearer_token = None):
    message = message.replace("Assistant:", "").strip()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": message}
    ]
    payload = {
    "model": api_name,
    "messages": messages,
    "max_tokens": max_new_tokens,
    "n": 1
    }
    key = API_key
    headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": key
    }
    url = "https://api.siliconflow.cn/v1/chat/completions"
    response = requests.post(url, json=payload, headers=headers)
    response = json.loads(response.text)
    choices = response['choices']
    res = choices[0]['message']['content']
    return res



class AgentAction:
    def __init__(self, chatbot, template, parser_fn, max_new_tokens=128,
                 api_name =None,
                 api_bearer_token = None):
        '''
        api_name: str, the name of the api (use siliconflow free API = =), if api is empty, use chatbot to respond
        '''
        self.api_bearer_token = api_bearer_token
        self.api_name = api_name
        self.api_bearer_token = api_bearer_token
        if(not api_name):
            print('using HF chatbot to respond...')
            self.chatbot = chatbot
        else:
            print('using siliconflow API to respond...')
        self.template = self.load_template(template)
        self.parse_fn = parser_fn
        self.max_new_tokens = max_new_tokens

    def load_template(self, path):
        with open(path, "r", encoding="utf-8") as f:
            template = f.read()
        return template

    def complete(self, **kwargs):
        message = self.template.format(**kwargs)
        # print(message)
        if(not self.api_name):
            ### HF models
            response = self.chatbot.respond(message, self.max_new_tokens)
            # print(response)
        else:
            ### use api
            for _ in range(5):
                try:
                    response = respond_via_api(message, api_name = self.api_name,   max_new_tokens= self.max_new_tokens, api_bearer_token = self.api_bearer_token)
                    break
                except KeyboardInterrupt:
                    print("\nKeyboardInterrupt caught. Exiting the program.")
                    #sys.exit(-1)
                    os._exit(-1)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    print("api error encountered, retrying...")
                    continue
        ## TODO : complete the parsing
        parserd_response = self.parse_fn(response)
        return parserd_response


class AgentSearch:
    def __init__(self, kb, agent):
        self.kb = kb
        self.trie = self.build_trie()
        self.kb_keys = list(kb.keys())
        self.kb_keys = [key.strip() for key in self.kb_keys]
        self.kb_context = [kb[key]["text"].strip().replace("\n", " ") for key in self.kb.keys()]
        corpus = [text.split() for text in self.kb_context]
        self.bm25 = BM25(corpus)
        self.agent = agent

    def build_trie(self):
        trie = Trie("", "")
        for value in self.kb.values():
            text = value["text"]
            trie.add_sons(text)
        return trie

    def look_up_trie(self, id_seq):
        output = " ".join(self.trie.search_content(id_seq))
        if output:
            content = [f"{id_seq} - {output}"]
        else:
            content = []
        return content

    def look_up_sons(self, id_seq):
        sons = self.trie.search_sons(id_seq)
        son_ids = list(sons.keys())
        son_ids = [id_seq + id for id in son_ids]
        return son_ids

    def decode_sons(self, sons):
        # sons is list(item_nums)
        # sons = [list(son.keys()) for son in sons]
        sons = [s for son in sons for s in son]
        content = []
        for son in sons:
            son_content = " ".join(self.trie.search_content(son))
            content.append(f"{son} - {son_content}")
        return content

    def search_beam_law(self, event, max_law_items, max_depth, generation_steps=5):
        # 在这里完成整个search的过程， 暂时这样，如果出错就从头开始
        # params: event, candiadtes,
        # 总共有两部分，1.look up further, 2.selected
        # beam呈累增的形式
        selected_law_items = []
        # look_up_law_items = []
        look_up_pool_size = 1
        selected_pool_size = 1
        sons = [self.look_up_sons("")]
        candidates = self.decode_sons(sons)
        for _ in range(max_depth):
            look_up, selected = [], []
            for __ in range(generation_steps):
                try:
                    selected, look_up = self.agent.complete(event=event, candidates=" \n".join(candidates),
                                                            look_up_pool_size=look_up_pool_size,
                                                            selected_pool_size=selected_pool_size)
                    break
                except:
                    continue
            selected_law_items += selected[:selected_pool_size]
            selected_law_items = list(set(selected_law_items))
            if len(selected_law_items) >= max_law_items: break
            if not look_up: break
            # look_up_law_items = [item for item in look_up]

            look_up_pool_size = min(max_law_items, look_up_pool_size + 1)
            selected_pool_size = min(max_law_items - len(selected_law_items), selected_pool_size + 1)
            sons = [self.look_up_sons(f) for f in look_up]
            candidates = self.decode_sons(sons)
        selected_laws = []
        for item in selected_law_items[:max_law_items]:
            trie_item = self.look_up_trie(item)
            if trie_item:
                selected_laws.append(trie_item[0])
        return selected_laws

    def look_up_section(self, section):
        contents = []

        clean_section = section.replace("§", "").strip()
        if clean_section in self.kb:
            context = self.kb[clean_section]["text"].strip().replace('\n', '')
            contents.append(f"{section}: {context}")

        return contents

    def search_related_regulations(self, content, num=5):
        regulations = []
        if isinstance(content, list):
            content = " ".join(content)
        content = content.split(" ")
        score_index = self.bm25.get_scores(content)
        score_index = sorted(score_index, key=lambda x: x[0], reverse=True)[:num]
        index = [si[1] for si in score_index]
        for idx in index:
            regulations.append(f"{self.kb_keys[idx]} - {self.kb_context[idx]}")
        return regulations


class AgentsIdSearch:
    def __init__(self, chatbot, args, parser):
        self.lawyer_agent = AgentAction(chatbot, args.law_template,
                                        parser.parse_law, args.lawyer_tokens, api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_filter_agent = AgentAction(chatbot, args.law_filter_template,
                                           parser.parse_law_filter, args.law_filter_tokens, api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.search_agent = AgentSearch(args.kb, self.lawyer_agent)
        self.decision_agent = AgentAction(chatbot, args.decision_making_template,
                                          parser.parse_decision, args.decision_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_generation_round = args.law_generation_round
        self.law_filtering_round = args.law_filtering_round
        self.generation_round = args.generation_round
        self.max_law_items = args.max_law_items


    def action(self, event):
        # conclusion = self.conclusion_agent.complete(event=event)
        collected_candidates = []
        logging = {}
        for _ in range(self.law_generation_round):
            # laws = list(item_ids)
            for __ in range(self.generation_round):
                try:
                    laws = self.lawyer_agent.complete(event=event,
                                                  generated_num=self.max_law_items)[-self.max_law_items:]

                    for law in laws:
                        candidate = self.search_agent.look_up_trie(law)
                        if candidate:
                            collected_candidates.append(candidate[0])
                    break
                except: continue

        collected_candidates = list(set(collected_candidates))
        filtered_candidates = []
        logging["filter_response"] = []
        for _ in range(self.law_filtering_round):
            for __ in range(self.generation_round):
                try:
                    filtered_laws = self.law_filter_agent.complete(event=event, candidates="\n".join(collected_candidates))
                    logging["filter_response"].append(filtered_laws["response"])
                    filtered_candidates.append(filtered_laws["filtered"])
                    break
                except: continue

        filtered_laws_item_number = list_intersection(filtered_candidates)
        filtered_laws = []
        for item_number in filtered_laws_item_number:
            item = self.search_agent.look_up_trie(item_number)
            if item:
                filtered_laws.append(item[0])
        # filtered_laws = [[0]  for law in filtered_laws]
        logging["filtered_laws"] = filtered_laws
        for _ in range(self.generation_round):

            try:
                decision = self.decision_agent.complete(event=event,
                                                        reference_regulations="\n".join(filtered_laws))
                logging["decision"] = decision["decision"]
                logging["decision_response"] = decision["response"]
                break
            except:
                continue
        return logging


class AgentTrieSearch:

    def __init__(self, chatbot, args, parser):

        self.lawyer_agent = AgentAction(chatbot, args.law_template,
                                        parser.parse_law_beam, args.lawyer_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_filter_agent = AgentAction(chatbot, args.law_filter_template,
                                           parser.parse_law_filter, args.law_filter_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.search_agent = AgentSearch(args.kb, self.lawyer_agent)
        self.decision_agent = AgentAction(chatbot, args.decision_making_template,
                                          parser.parse_decision, args.decision_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)


        self.law_generation_round = args.law_generation_round
        self.law_filtering_round = args.law_filtering_round
        self.generation_round = args.generation_round
        self.max_law_items = args.max_law_items
        self.max_depth = args.max_depth

    def action(self, event):
        collected_candidates = []
        logging = {}
        for _ in range(self.law_generation_round):
            candidates = self.search_agent.search_beam_law(event, self.max_law_items, self.max_depth,
                                                           self.generation_round)
            collected_candidates += candidates

        filtered_candidates = []
        logging["filter_response"] = []
        for _ in range(self.law_filtering_round):
            for __ in range(self.generation_round):
                try:
                    filtered_laws = self.law_filter_agent.complete(event=event, candidates="\n".join(collected_candidates))
                    logging["filter_response"].append(filtered_laws["response"])
                    filtered_candidates.append(filtered_laws["filtered"])
                    break
                except: continue

        filtered_laws_item_number = list_intersection(filtered_candidates)
        filtered_laws = []
        for item_number in filtered_laws_item_number:
            item = self.search_agent.look_up_trie(item_number)
            if item:
                filtered_laws.append(item[0])
        # filtered_laws = [[0]  for law in filtered_laws]

        for _ in range(self.generation_round):
            # decision = {decision:"yes/no", reason:"xxx"}
            try:
                decision = self.decision_agent.complete(event=event,
                                                        reference_regulations="\n".join(filtered_laws))
                logging["decision"] = decision["decision"]
                logging["decision_response"] = decision["response"]
                break
            except:
                continue
        return logging

class AgentContentSearch:
    def __init__(self, chatbot, args, parser):

        self.lawyer_agent = AgentAction(chatbot, args.law_template,
                                        parser.parse_law_content, args.lawyer_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_filter_agent = AgentAction(chatbot, args.law_filter_template,
                                           parser.parse_law_filter, args.law_filter_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_judge_agent = AgentAction(chatbot, args.law_judge_template,
                                           parser.parse_law_judge, args.law_judge_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.search_agent = AgentSearch(args.kb, self.lawyer_agent)
        self.decision_agent = AgentAction(chatbot, args.decision_making_template,
                                          parser.parse_decision, args.decision_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_generation_round = args.law_generation_round
        self.law_filtering_round = args.law_filtering_round
        self.generation_round = args.generation_round
        self.max_law_items = args.max_law_items
        self.look_up_items = args.look_up_items

    def action(self, event):
        collected_candidates = []
        logging = {}
        for _ in range(self.law_generation_round):
            for __ in range(self.generation_round):
                try:
                    content = self.lawyer_agent.complete(event=event)
                    searched_items = self.search_agent.search_related_regulations(content, self.look_up_items)
                    collected_candidates += searched_items
                    break
                except: continue
        collected_candidates = list(set(collected_candidates))
        filtered_candidates = []
        logging["filter_response"] = []
        for _ in range(self.law_filtering_round):
            for __ in range(self.generation_round):
                try:
                    filtered_laws = self.law_filter_agent.complete(event=event, candidates="\n".join(collected_candidates))
                    logging["filter_response"].append(filtered_laws["response"])
                    filtered_candidates.append(filtered_laws["filtered"])
                    break
                except: continue

        filtered_laws_item_number = list_intersection(filtered_candidates)
        filtered_laws = []
        for item_number in filtered_laws_item_number:
            item = self.search_agent.look_up_trie(item_number)
            if item:
                filtered_laws.append(item[0])
        # filtered_laws = [[0]  for law in filtered_laws]
        logging["filtered_laws_coarse"] = filtered_laws
        filtered_laws_coarse = copy.deepcopy(filtered_laws)
        filtered_laws = []

        for law in filtered_laws_coarse:
            for _ in range(self.generation_round):
                try:
                    judge = self.law_judge_agent.complete(event=event, candidate_law=law)
                    if judge["decision"] == "yes":
                        filtered_laws.append(law)
                    break
                except:continue

        for _ in range(self.generation_round):
            try:
                decision = self.decision_agent.complete(event=event,
                                                        reference_regulations="\n".join(filtered_laws))
                logging["decision"] = decision["decision"]
                logging["decision_response"] = decision["response"]
                break
            except:
                continue
        return logging








class AgentEmbSearch:
    def __init__(self, chatbot, args, parser):
        if args.parse_1by1:
            filter_parser = parser.parse_yes_no
        else:
            filter_parser = parser.parse_law_filter
    
        self.lawyer_agent = AgentAction(chatbot, args.law_template,
                                        parser.parse_law_content, args.lawyer_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_filter_agent = AgentAction(chatbot, args.law_filter_template,
                                           filter_parser, args.law_filter_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_judge_agent = AgentAction(chatbot, args.law_judge_template,
                                           parser.parse_law_judge, args.law_judge_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.search_agent = AgentSearch(args.kb, self.lawyer_agent)
        self.decision_agent = AgentAction(chatbot, args.decision_making_template,
                                          parser.parse_decision, args.decision_tokens, 
                                          api_name= args.api_name,
                         api_bearer_token = args.api_bearer_token)
        self.law_generation_round = args.law_generation_round
        self.law_filtering_round = args.law_filtering_round
        self.generation_round = args.generation_round
        self.max_law_items = args.max_law_items
        self.look_up_items = args.look_up_items


    def parepare_regulation_text(self, rule):
        '''
        For each rule's key (dict), covert it to a list of string 
        '''
        def id_exist(id, id_list):
            for i in id_list:
                if id in i:
                    return True
            return False
        id_ret = []
        text_ret = []
        for id in rule:
            if(id_exist(id, id_ret)):
                continue
            root_text = rule[id]['root_text']
            sub_ids = rule[id]['sub_rules']
            sub_texts = rule[id]['sub_text']
            ret = root_text
            for i, sub_id in enumerate(sub_ids):
                sub_text = sub_texts[i]
                ret += f'\n{sub_id} {sub_text}'
            id_ret.append(id)
            text_ret.append(ret)

        return id_ret, text_ret
    
    def action(self, event_dict, use_gt):
        emb_dict = event_dict['semantic_rules']
        gt_dict = event_dict['gt_rules']
        event = event_dict['context']
        if use_gt:
            used_regulation = gt_dict
        else:
            used_regulation = emb_dict

        id_ret, text_ret = self.parepare_regulation_text(used_regulation)
        filtered_idx = []
        for i, content in enumerate(text_ret):
            try:
                candidates = id_ret[i] + '-- ' + content
                filtered_result = self.law_filter_agent.complete(event=event, candidates = candidates)
                decision = filtered_result['decision']
                if decision == 'yes':
                    filtered_idx.append(i)
            except:
                continue
        filtered_laws = []
        for i in filtered_idx:
            item_numer = id_ret[i]
            item = self.search_agent.look_up_trie(item_numer)
            if item:
                filtered_laws.append(item[0])
        logging = {}
        for _ in range(self.generation_round):
            try:
                decision = self.decision_agent.complete(event=event,
                                                        reference_regulations="\n".join(filtered_laws))
                logging["decision"] = decision["decision"]
                logging["decision_response"] = decision["response"]
                break
            except:
                continue
        return logging


