import json
import os

def read_medical_history(name):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    return data["medical_history"]

def write_medical_history(name, new_info):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    data["medical_history"].append(new_info)
    with open(f'users/{name}.json', 'w') as f:
        json.dump(data, f, indent=0)

def append_doctor_notes(name, new_doctor_notes):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    data["doctor_notes"].append(new_doctor_notes)
    with open(f'users/{name}.json', 'w') as f:
        json.dump(data, f, indent=0)

def read_doctor_notes(name):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    return data["doctor_notes"]
