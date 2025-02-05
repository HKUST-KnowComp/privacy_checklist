#!/bin/bash

# Arguments to pass to the Python script
ARG1="--events_path data/HIPAA/eval_generate.csv"
#mistralai/Mistral-7B-Instruct-v0.2
#Qwen/Qwen2-7B-Instruct
ARG2="--api_name THUDM/glm-4-9b-chat"
ARG3="--api_bearer_token xxxxx"

#for i in {1..5}
#do
i=1
python search_content_for_answer_HIPAA.py  --log_path logs/bm25_content/glm-4-9b-chat--direct_answer--generate--$i.txt  $ARG1 $ARG2 $ARG3

#done 275--257