#!/bin/bash

# Arguments to pass to the Python script
ARG1="--events_path data/HIPAA/eval_generate.csv"
ARG2="--api_name Qwen/Qwen2-7B-Instruct"


for i in {2..5}
do

    python direct_answer_HIPAA.py  --log_path logs/dp/Qwen2-7B-Instruct--direct_answer--generate--$i.txt  $ARG1 $ARG2
done