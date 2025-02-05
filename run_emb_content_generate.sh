#!/bin/bash

# Arguments to pass to the Python script
ARG1="--events_path data/HIPAA/eval_generate.csv"
#mistralai/Mistral-7B-Instruct-v0.2
#Qwen/Qwen2-7B-Instruct
ARG2="--api_name THUDM/glm-4-9b-chat"
ARG3="--api_bearer_token xxxx"

#for i in {1..5}
#do
i=1
python emb_sim_search.py  --log_path logs/emb_content/glm-4-9b-chat--direct_answer--generate--$i.txt  --use_gt False $ARG1 $ARG2
#done