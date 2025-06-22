import json

def read_medical_history(name):
    """
    Write the medical history to a file.
    """
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    return data["medical_history"]

def write_medical_history(name, new_info):
    """
    Read the medical history from a file.
    """
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    data["medical_history"].append(new_info)
    with open(f'users/{name}.json', 'w') as f:
        json.dump(data, f, indent=0)
    
def append_doctor_notes(name, new_doctor_notes):
    """
    Append the doctor's notes to a file.
    """
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    data["doctor_notes"].append(new_doctor_notes)
    with open(f'users/{name}.json', 'w') as f:
        json.dump(data, f, indent=0)

def read_doctor_notes():
    """
    Read the doctor's notes from a file.
    """
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    return data["doctor_notes"]
