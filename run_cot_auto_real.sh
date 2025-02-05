#!/bin/bash


# Arguments to pass to the Python script
ARG1="--events_path data/HIPAA/eval_real.csv"
#Qwen/Qwen2-7B-Instruct
ARG2="--api_name THUDM/glm-4-9b-chat"
ARG3="--api_bearer_token xxxxx"

#for i in {1..5}
#do
i=1
    python cot_auto_answer_HIPAA.py  --log_path logs/cot_auto/glm-4-9b-chat--direct_answer--real--$i.txt   $ARG1 $ARG2 
#done