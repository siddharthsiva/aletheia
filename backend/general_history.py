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

def read_doctor_notes(name):
    """
    Read the doctor's notes from a file.
    """
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    return data["doctor_notes"]

def append_user_stats(name, bmi, height, bp):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    # Ensure the keys exist
    if 'bmi' not in data:
        data['bmi'] = []
    if 'height' not in data:
        data['height'] = []
    if 'bp' not in data:
        data['bp'] = []
    # Only append if values are not empty
    if bmi:
        data['bmi'].append(bmi)
    if height:
        data['height'].append(height)
    if bp:
        data['bp'].append(bp)
    with open(f'users/{name}.json', 'w') as f:
        json.dump(data, f, indent=0)

def read_user_stats(name):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    return data['bmi'], data['height'], data['bp']

def append_medication(name, medication, medication_time):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    if 'medications' not in data:
        data['medications'] = []
    if 'medication_times' not in data:
        data['medication_times'] = []
    if medication:
        data['medications'].append(medication)
        data['medication_times'].append(medication_time)
    if medication:
        # Convert time object to string if needed
        if isinstance(medication_time, time):
            med_time_str = medication_time.strftime("%H:%M")
        else:
            med_time_str = str(medication_time)
        data['medications'].append(medication)
        data['medication_times'].append(med_time_str)
    with open(f'users/{name}.json', 'w') as f:
        json.dump(data, f, indent=0)

def read_user_medications(name):
    with open(f'users/{name}.json', 'r') as f:
        data = json.load(f)
    return data['medications']