import json
from prompts import prompt_with_context, prompt_without_context, prompt_without_context_COT
import sys
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
os.environ['HF_HOME'] = '/private/workspace/fed_user_fedllm/LLMs'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
access_token = "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"
os.environ['HF_TOKEN'] =access_token
from transformers import AutoModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers
import torch
import logging
import argparse

dir_path = os.path.dirname(os.path.abspath(__file__))
print(f'dir_path: {dir_path}')



def read_data(path):
    with open(path, 'r') as f:
        data = json.load(f)

    return data

def save_to_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)



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


def main(data_path, model_name, prompt_type):
    if model_name == 'llama3-8b':
        model_id = 'meta-llama/Meta-Llama-3-8B-Instruct'
        model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")
    elif model_name == 'llama3-70b':
        model_id = 'meta-llama/Meta-Llama-3-70B-Instruct'
        model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto",torch_dtype = torch.bfloat16)
    elif model_name == 'mistrail-8x7b':
        model_id = 'mistralai/Mixtral-8x7B-Instruct-v0.1'
        model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto",torch_dtype = torch.bfloat16)
    else:
        raise ValueError('Invalid model')
    ### load models
    print(f'Loading model done: {model_id}')
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    pipeline = transformers.pipeline(
        "text-generation",
        model=model,
        tokenizer = tokenizer,
        #device="cuda",
    )
    pipeline.tokenizer.pad_token_id = pipeline.model.config.eos_token_id

    if(prompt_type == 'prompt_with_context'):
        main_prompt_with_context(data_path, model_name, pipeline)
    elif(prompt_type == 'prompt_without_context'):
        main_prompt_without_context(data_path, model_name, pipeline)
    else:
        raise ValueError('Invalid prompt type')

def llm_response(prompt, pipeline):

    msg = [
                {"role": "system", "content": "You are a legal expert that answers question as simple as possible."},
                {"role": "user", "content": prompt}
            ]
    msg_chat = pipeline.tokenizer.apply_chat_template(
        msg, 
        tokenize=False, 
        add_generation_prompt=True,
    )
    terminators = [
    pipeline.tokenizer.eos_token_id,
    pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]
    ### greedy decoding
    outputs = pipeline(
        msg_chat,
        max_new_tokens=512,
        eos_token_id=terminators,
        #do_sample=True,
        #temperature=0.6,
        #top_p=0.9,
        #batch_size=2
        do_sample= False,
        num_beams=1,
    )
    res = outputs[0]["generated_text"][len(msg_chat):]
    return res


def main_prompt_with_context(data_path, model, pipeline):

    ###
    
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
            res = llm_response(prompt, pipeline)
            response_list = [res]
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
            print(f'Finish {i} cases')

        #### prepare for prompt_without_context
        
    
    save_to_json(prompt_with_context_cases, save_path.replace('.json', f'_prompt_with_context.json'))


    


def main_prompt_without_context(data_path, model, pipeline):
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

        res = llm_response(prompt, pipeline)
        response = [res]
        temp_case = {
                'case_id': i,
                'prompt': prompt,
                'response': response,
                'COT_response': ''
            }
        ### for COT case
        res = llm_response(prompt_COT, pipeline)
        response = [res]
        if(res == -1):
            print('---------------------------')
            print('fail case')
            fail_cases.append({
                'type': 'prompt_without_context',
                'case_id': i,
                'prompt': prompt
            })
            continue
        temp_case['COT_response'] = response
        prompt_with_context_cases.append(temp_case)
        if(i % 2 == 0):
            save_to_json(prompt_with_context_cases, save_path)
            
        print(f'Finish {i} cases')
    
    save_to_json(prompt_with_context_cases, save_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='llama3-8b')
    parser.add_argument('--data_type', type=str, default='real')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--prompt_type', type=str, default='prompt_without_context')

    args = parser.parse_args()
    if(args.data_type == 'real'):
        data_path = os.path.join(dir_path,'real.json')
    else:
        raise ValueError('Invalid data type')
    model = args.model
    assert model in ['llama3-8b','llama3-70b','mistrail-8x7b']
    assert args.prompt_type in ['prompt_with_context', 'prompt_without_context','prompt_with_context_single']
    main(data_path, model, args.prompt_type)