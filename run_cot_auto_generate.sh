#!/bin/bash

# Arguments to pass to the Python script
ARG1="--events_path data/HIPAA/eval_generate.csv"
ARG2="--api_name Qwen/Qwen2-7B-Instruct"


for i in {1..5}
do

    python cot_auto_answer_HIPAA.py  --log_path logs/cot_auto/Qwen2-7B-Instruct--direct_answer--generate--$i.txt  $ARG1 $ARG2
done