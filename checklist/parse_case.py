import checklist.path_config as path_config
import pandas as pd
import ast

def read_csv_to_dict(file_path):
    '''
    Read a CSV file into a list of dictionaries
    '''
    df = pd.read_csv(file_path)
    # Convert the DataFrame into a list of dictionaries
    list_of_dicts = df.to_dict(orient='records')
    return list_of_dicts


'''
Process the generate cases and real cases and uniform them into the same format

refer_ids: a list of id_s
sender (sender's role)
subject (subject's role)
recipient (recipient's role)
norm_type (permit/forbid/not applicable)
context (the description of the content)
information_type
purpose
'''
def read_generate_cases():
    generate_case_path = path_config.generate_case_path
    cases = read_csv_to_dict(generate_case_path)
    ret = []
    for case in cases:
        temp_dict = {}
        #characteristics = ast.literal_eval(case['generate_characteristics'])
        #temp_dict['refer_ids'] = ast.literal_eval(case['generate_regulation_ids'])
        # temp_dict['refer_ids'] = ast.literal_eval(case['refer_ids'])
        # temp_dict['sender'] = characteristics['Sender Role']
        # temp_dict['subject'] = characteristics['About Role']
        # temp_dict['recipient'] = characteristics['Recipient Role']

        temp_dict['refer_ids'] = ast.literal_eval(case['refer_ids'])
        temp_dict['sender'] = case['sender']
        temp_dict['subject'] = case['subject']
        temp_dict['recipient'] = case['recipient']

        norm_type = case['norm_type']
        temp_dict['norm_type'] = norm_type
        assert norm_type in ['positive_norm', 'negative_norm', 'not applicable']
        temp_dict['context'] = case['context']
        temp_dict['information_type'] = case['information_type']
        temp_dict['purpose'] = case['purpose']
        # if norm_type.lower() == 'permit':
        #     temp_dict['norm_type'] = 'positive_norm'
        # elif norm_type.lower() == 'forbid':
        #     temp_dict['norm_type'] = 'negative_norm'
        # else:
        #     temp_dict['norm_type'] = 'not applicable'
        # temp_dict['context'] = case['generate_background']
        # temp_dict['information_type'] = characteristics['Type']
        # temp_dict['purpose'] = characteristics['Purpose']
        ret.append(temp_dict)
    return ret


def read_real_cases():
    real_case_path = path_config.real_case_path
    cases = read_csv_to_dict(real_case_path)
    ret = []
    for case in cases:
        temp_dict = {}
        # characteristics =  ast.literal_eval(case['generate_characteristics'])
        # temp_dict['refer_ids'] = ast.literal_eval(case['refer_ids'])
        # ### temp_dict['refer_ids'] = ast.literal_eval(case['generate_regulation_ids'])  ## list of regulation ids refer_ids
        # temp_dict['sender'] = characteristics['Sender Role']
        # temp_dict['subject'] = characteristics['About Role']
        # temp_dict['recipient'] = characteristics['Recipient Role']
        # norm_type = case['generate_HIPAA_type']
        # if norm_type.lower() == 'permit':
        #     temp_dict['norm_type'] = 'positive_norm'
        # elif norm_type.lower() == 'forbid':
        #     temp_dict['norm_type'] = 'negative_norm'
        # else:
        #     temp_dict['norm_type'] = 'not applicable'
        # temp_dict['context'] = case['generate_background']
        # temp_dict['information_type'] = characteristics['Type']
        # temp_dict['purpose'] = characteristics['Purpose']

        temp_dict['refer_ids'] = ast.literal_eval(case['refer_ids'])
        temp_dict['sender'] = case['sender']
        temp_dict['subject'] = case['subject']
        temp_dict['recipient'] = case['recipient']

        norm_type = case['norm_type']
        temp_dict['norm_type'] = norm_type
        assert norm_type in ['positive_norm', 'negative_norm', 'not applicable']
        temp_dict['context'] = case['context']
        temp_dict['information_type'] = case['information_type']
        temp_dict['purpose'] = case['purpose']

        ret.append(temp_dict)
    return ret

def get_cases(type):
    if type == 'generate':
        return read_generate_cases()
    elif type == 'real':
        return read_real_cases()
    else:
        raise NotImplementedError

'''
text processing should end here
'''


if __name__ == '__main__':
    from pprint import pprint
    generate = read_generate_cases()
    real = read_real_cases()
    pprint(generate[0])
    print('done')
    pprint(real[0])