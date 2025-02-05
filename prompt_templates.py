prompt_without_refer = '''
As a legal expert specializing in the HIPAA Privacy Rule, your task is to read a specific paragraph of the regulation 
{id}:
{text}


Now complete the following questions one by one:

Q1. ("Prohibit","Permit" or "General Definition") Ascertain whether the regulation {id} pertains to scenes that are:
A. <Prohibit by law>
B. <Permit by law>
C. <General Definition>

Q2. (Indentify the stakeholders related to regulation {id}) Identify the stakeholders related to the regulation {id}. Your response must include the following seven characteristics about the flow of private information: [Sender, Sender Role, Recipient, Recipient Role, Subject, Subject Role, Information Type, Consent Form, Purpose]. Answer 'None' if no information about characteristics are present.

The "Sender", "Recipient" and "Subject" ﬁelds indicate the sender, recipient and the data subject during information transmission.
The "Sender Role", "Recipient Role" and "Subject Role" ﬁelds indicate the role of the sender, recipient and subject (e.g., doctor, patient).
The "Information Type" ﬁeld deﬁnes what kind of information would be passed, such as name or location.
The "Consent Form" ﬁeld indicates whether the sender has obtained consent from the subject to send the message. If consent is required, you should answer "Consent" for a flexible requirement or "Authorization" for a formal and mandatory process required by context. If consent is not related to the context, you should answer "None".
The "Purpose" ﬁeld indicates the purpose of mentioned information transmission such as treatment, payment, or health care operations. 

Q3: Is Sender and Subject the same person?
A. <YES>
B. <NO>
C. <Not Sure>

Q4: Is Recipient and Subject the same person?
A. <YES>
B. <NO>
C. <Not Sure>
'''




prompt_with_refer = '''
As a legal expert specializing in the HIPAA Privacy Rule, your task is to read a specific paragraph of the regulation 
{id}:
{text}


Now complete the following questions one by one:

Q1. ("Prohibit","Permit" or "General Definition") Ascertain whether the regulation {id} pertains to scenes that are:
A. <Prohibit by law>
B. <Permit by law>
C. <General Definition>

Q2. (Indentify the stakeholders related to regulation {id}) Identify the stakeholders related to the regulation {id}. Your response must include the following seven characteristics about the flow of private information: [Sender, Sender Role, Recipient, Recipient Role, Subject, Subject Role, Information Type, Consent Form, Purpose]. Answer 'None' if no information about characteristics are present.

The "Sender", "Recipient" and "Subject" ﬁelds indicate the sender, recipient and the data subject during information transmission.
The "Sender Role", "Recipient Role" and "Subject Role" ﬁelds indicate the role of the sender, recipient and subject (e.g., doctor, patient).
The "Information Type" ﬁeld deﬁnes what kind of information would be passed, such as name or location.
The "Consent Form" ﬁeld indicates whether the sender has obtained consent from the subject to send the message. If consent is required, you should answer "Consent" for a flexible requirement or "Authorization" for a formal and mandatory process required by context. If consent is not related to the context, you should answer "None".
The "Purpose" ﬁeld indicates the purpose of mentioned information transmission such as treatment, payment, or health care operations. 

Q3: Is Sender and Subject the same person?
A. <YES>
B. <NO>
C. <Not Sure>

Q4: Is Recipient and Subject the same person?
A. <YES>
B. <NO>
C. <Not Sure>

Q5. (Identify the relation between {id} other parts referred in the context) Identify the relation between {id} and referred {refer_list}. For each reference in {refer_list}, according to the context given, determine if the reference is an exception of {id} or support argument of {id}. Answer with "<Exception>" or "<Support>" for each reference.

'''