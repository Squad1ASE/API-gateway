import json

user_columns = ['email','phone','firstname','lastname','password','dateofbirth','role']

def user_to_json(form_dict):

    user_dict = dict(
        (k,form_dict[k]) 
        for k in form_dict.keys() if k in user_columns
    )
    
    return json.dumps(user_dict)