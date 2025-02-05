'''
3 prompts are included
1): prompt_with_context: This prompt is used when the regulation text is provided along with the case text. The expert is asked to answer questions based on the regulation and the case.

2) prompt_with_context_single: This prompt is used when the regulation text is provided along with the case text. The difference here is that there is only 1 regulation included.

2): prompt_without_context: This prompt is used when the regulation text is not provided. The expert is asked to answer questions based on the case only.

3): prompt_without_context_COT: This prompt is used when the regulation text is not provided. The expert is asked to answer questions based on the case only. In this prompt, the expert is also asked to identify the stakeholders related to the case.
'''

prompt_with_context ='''
As a legal expert specializing in the HIPAA Privacy Rule, your task is to read a specific paragraph of the regulation and one case scenario. You will be asked to answer questions based on the regulation and the case.



HIPAA Regulation:
{regulation_text}



Case:
{case_text}



Extracted information from the case:
{case_stat_str}

Now complete the following questions one by one, you should answer precisely.



Q1. (Correctness of Extracted Info from the case) Ascertain whether the "Extracted information from the case" is consistent with the case. If no, identify the correct information:
A. <YES>
B. <NO>
C. <Not Sure>

Q2. Is the HIPAA regulation relevant to determine privacy violation? If no, explain why.
A. <YES>
B. <NO>
C. <Not Sure>

Q3. Does given case violates its subject's privacy? First answer the question and then explain why.
A. <YES>
B. <NO>
C. <The Case is Not Relevant with HIPAA>
'''








prompt_with_context_single ='''
As a legal expert specializing in the HIPAA Privacy Rule, your task is to read a specific paragraph of the regulation and one case scenario. You will be asked to answer questions based on the regulation and the case.



HIPAA Regulation {id}:
{regulation_text}



Extracted information from the regulation:
{regulation_stat_str}



Case:
{case_text}



Extracted information from the case:
{case_stat_str}

Now complete the following questions one by one, you should answer precisely.

Q1. (Correctness of Extracted Info from the regulation) Ascertain whether the "sender", "receiver" and "subject" from "Extracted information from the regulation" are consistent with the regulation text. If no, identify the correct information:
A. <YES>
B. <NO>
C. <Not Sure>

Q2. (Correctness of Extracted Info from the case) Ascertain whether the "Extracted information from the case" is consistent with the case. If no, identify the correct information:
A. <YES>
B. <NO>
C. <Not Sure>

Q3: Is the HIPAA regulation relevant to determine privacy violation? If no, explain why.
A. <YES>
B. <NO>
C. <Not Sure>

Q4. Does given case violates its subject's privacy? First answer the question and then explain why.
A. <YES>
B. <NO>
C. <The Case is Not Relevant with HIPAA>
'''











prompt_without_context ='''
As a legal expert specializing in the HIPAA Privacy Rule, your task is to read a specific paragraph of the regulation and one case scenario. You will be asked to answer questions based on the given case.



Case:
{case_text}


Now complete the following questions one by one, you should answer precisely.



Q1. Does given case violates its subject's privacy? First answer the question and then explain why.
A. <YES>
B. <NO>
C. <The Case is Not Relevant with HIPAA>
'''



prompt_without_context_COT ='''
As a legal expert specializing in the HIPAA Privacy Rule, your task is to read a specific paragraph of the regulation and one case scenario. You will be asked to answer questions based on the given case.



Case:
{case_text}


Now complete the following questions one by one, you should answer precisely.

Q1. (Indentify the stakeholders related to the given case). Identify the stakeholders related to the case. Your response must include the following characteristics about the flow of private information: [Sender, Sender Role, Recipient, Recipient Role, Subject, Subject Role, Information Type]. Answer 'None' if no information about characteristics are present. 
The "Sender", "Recipient" and "Subject" ﬁelds indicate the sender, recipient and the data subject during information transmission.
The "Sender Role", "Recipient Role" and "Subject Role" ﬁelds indicate the role of the sender, recipient and subject (e.g., doctor, patient).
The "Information Type" ﬁeld deﬁnes what kind of information would be passed, such as name or location.


Q2. Based on your answer for Q1, determine if the given case violates its subject's privacy? First answer the question and then explain why.
A. <YES>
B. <NO>
C. <The Case is Not Relevant with HIPAA>
'''