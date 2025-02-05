import json
from prompts import prompt_with_context, prompt_without_context, prompt_without_context_COT
import sys
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
## go to parent directory
base_path = os.path.dirname(dir_path)
sys.path.append(base_path)
from utils import chat_with_backoff
import openai
### setup azure api
openai.api_type ="azure"
openai.api_base ="https://hkust.azure-api.net"
openai.api_version ="2023-05-15"
openai.api_key = 'e89ab7c922c94d2eb6c88ef67f7547d6'

def read_data(path):
    with open(path, 'r') as f:
        data = json.load(f)

    return data

def save_to_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def parse_res(res, num_msg):
    ret = []
    for i in range(num_msg):
        #print(f'i: {i}')
        cur_res = res["choices"][i]["message"]['content']
        ret.append(cur_res)
    return ret

def prepare_rule_string(rule):
    '''
    For each rule's key (dict), covert it to a list of string 
    '''
    id_ret = []
    text_ret = []
    for id in rule:
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


def prepare_prompt_with_context(case_id, case_text, gt_rules, semantic_rules, case_stat_str):
    '''
    Prepare the prompt for the given case
    '''
    gt_ids, gt_texts = prepare_rule_string(gt_rules)
    semantic_ids, semantic_texts = prepare_rule_string(semantic_rules)
    prompt_list = []
    for i, regu_text in enumerate(gt_texts):
        source = 'gt_rules'
        regu_id = gt_ids[i]
        prompt = prompt_with_context.format(case_text=case_text, regulation_text=regu_text, case_stat_str = case_stat_str)
        prompt_list.append([case_id,regu_id, source, prompt])

    for i, regu_text in enumerate(semantic_texts):
        source = 'semantic_rules'
        regu_id = semantic_ids[i]
        prompt = prompt_with_context.format(case_text=case_text, regulation_text=regu_text, case_stat_str = case_stat_str)
        prompt_list.append([case_id,regu_id, source, prompt])

    return prompt_list


def main(data_path, model):
    if model == 'gpt3.5':
        engine = 'gpt-3.5-turbo'
    elif model == 'gpt4':
        engine = 'gpt-4'
    else:
        raise ValueError('Invalid model')
    num_msg = 1
    cases = read_data(data_path)
    save_path = data_path.replace('.json', f'_judged_{model}.json')
    fail_path = data_path.replace('.json', f'_failed_{model}.json')

    fail_cases = []
    prompt_with_context_cases = []
    for i, case in enumerate(cases):
        case_text = case['context']
        gt_rules = case['gt_rules']
        semantic_rules = case['semantic_rules'] ### can be empty
        case_sender, case_subject, case_recipient = case['sender'], case['subject'], case['recipient']
        information_type = case['information_type']
        #case stats
        case_stat_str = f'Sender: {case_sender}\nSubject: {case_subject}\nRecipient: {case_recipient}\nInformation Type: {information_type}'


        #### prepare for prompt_with_context
        prompt_list = prepare_prompt_with_context(i, case_text, gt_rules, semantic_rules, case_stat_str)
        for id, regu_id, source, prompt in prompt_list:

            msg = [
                {"role": "system", "content": "You are a legal expert that answers question as simple as possible."},
                {"role": "user", "content": prompt}
            ]
            res = chat_with_backoff(engine=engine,
                        messages=msg, n = num_msg)
            if(res == -1):
                print('---------------------------')
                print('fail case')
                fail_cases.append({
                    'type': 'prompt_with_context',
                    'case_id': id,
                    'regu_id': regu_id,
                    'source': source,
                    'prompt': prompt
                })
                continue
            response_list = parse_res(res, num_msg)
            gpt_response = response_list        #let's save it a list for now
            prompt_with_context_cases.append({
                'case_id': id,
                'regu_id': regu_id,
                'source': source,
                'prompt': prompt,
                'response': gpt_response
            })
            if(i % 2 == 0):
                save_to_json(prompt_with_context_cases, save_path.replace('.json', f'_prompt_with_context.json'))
                save_to_json(fail_cases, fail_path.replace('.json', f'_prompt_with_context.json'))
            print(f'Finish {i} cases')

        #### prepare for prompt_without_context
        
    
    save_to_json(prompt_with_context_cases, save_path.replace('.json', f'_prompt_with_context.json'))
    save_to_json(fail_cases, fail_path.replace('.json', f'_prompt_with_context.json'))

    


def main_no_context(data_path, model):
    if model == 'gpt3.5':
        engine = 'gpt-3.5-turbo'
    elif model == 'gpt4':
        engine = 'gpt-4'
    else:
        raise ValueError('Invalid model')
    num_msg = 1
    cases = read_data(data_path)
    save_path = data_path.replace('.json', f'_judged_{model}_prompt_without_context.json')
    fail_path = data_path.replace('.json', f'_failed_{model}_prompt_without_context.json')

    fail_cases = []
    prompt_with_context_cases = []
    for i, case in enumerate(cases):
        case_text = case['context']
        gt_rules = case['gt_rules']
        semantic_rules = case['semantic_rules'] ### can be empty
        case_sender, case_subject, case_recipient = case['sender'], case['subject'], case['recipient']
        information_type = case['information_type']
        #case stats
        case_stat_str = f'Sender: {case_sender}\nSubject: {case_subject}\nRecipient: {case_recipient}\nInformation Type: {information_type}'


        #### prepare for prompt_without_context
        prompt = prompt_without_context.format(case_text=case_text)

        #### prepare for prompt_without_context_COT
        prompt_COT = prompt_without_context_COT.format(case_text=case_text)

        msg = [
                {"role": "system", "content": "You are a legal expert that answers question as simple as possible."},
                {"role": "user", "content": prompt}
            ]
        res = chat_with_backoff(engine=engine,
                    messages=msg, n = num_msg)
        if(res == -1):
            print('---------------------------')
            print('fail case')
            fail_cases.append({
                'type': 'prompt_without_context',
                'case_id': i,
                'prompt': prompt
            })
            continue
        response = parse_res(res, num_msg)
        temp_case = {
                'case_id': i,
                'prompt': prompt,
                'response': response,
                'COT_response': ''
            }
        ### for COT case
        msg = [
                {"role": "system", "content": "You are a legal expert that answers question as simple as possible."},
                {"role": "user", "content": prompt_COT}
            ]
        res = chat_with_backoff(engine=engine,
                    messages=msg, n = num_msg)
        if(res == -1):
            print('---------------------------')
            print('fail case')
            fail_cases.append({
                'type': 'prompt_without_context',
                'case_id': i,
                'prompt': prompt
            })
            continue
        response = parse_res(res, num_msg)
        temp_case['COT_response'] = response
        prompt_with_context_cases.append(temp_case)
        if(i % 2 == 0):
            save_to_json(fail_cases, fail_path)
            save_to_json(prompt_with_context_cases, save_path)
            
        print(f'Finish {i} cases')
    
    save_to_json(prompt_with_context_cases, save_path)
    save_to_json(fail_cases, fail_path)

if __name__ == '__main__':
    data_path = os.path.join(dir_path,'real.json')
    model = 'gpt4'
    assert model in ['gpt3.5', 'gpt4']
    main_no_context(data_path, model)