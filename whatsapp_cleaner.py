import re
import pandas as pd

def detect_and_clean_log(input_file_path):

    patterns = [
        re.compile(r'^\[?(\d{2}/\d{2}/\d{2,4}),\s(\d{2}:\d{2}(?::\d{2})?)\]?\s-\s([^:]+):\s(.*)$'),
        re.compile(r'^(\d{2}/\d{2}/\d{2,4}),\s(\d{1,2}:\d{2}\s*[A-Za-z]{2})\s-\s([^:]+):\s(.*)$'),
        re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{2}:\d{2})\s-\s([^:]+):\s(.*)$'),
        re.compile(r'^\[?(\d{4}-\d{2}-\d{2})\s(\d{2}:\d{2}:\d{2})\]?\s([^:]+):\s(.*)$')
    ]

    cleaned_records = []
    matched_pattern = None
    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(input_file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

    for line in lines[:100]:  # Sample the first 100 lines
        line_str = line.strip()
        if not line_str:
            continue
        for p in patterns:
            if p.match(line_str):
                matched_pattern = p
                break
        if matched_pattern:
            break

    if not matched_pattern:
        matched_pattern = re.compile(r'^(\d{2}/\d{2}/\d{2,4}),\s(\d{2}:\d{2})\s-\s([^:]+):\s(.*)$')

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        match = matched_pattern.match(line_str)
        if match:
            date_str, time_str, sender, message = match.groups()
            
            system_triggers = ["created group", "added you", "changed the group", "left the group", 
                               "was added", "end-to-end encrypted", "changed their phone", "omitted"]
            if any(trigger in message.lower() for trigger in system_triggers):
                continue
            
            cleaned_records.append({
                'raw_date': date_str,
                'raw_time': time_str,
                'sender': sender.strip(),
                'message': message.strip()
            })
        else:
            if cleaned_records:
                cleaned_records[-1]['message'] += " " + line_str

    if not cleaned_records:
        raise ValueError("Could not extract structured log profiles. Format is unrecognized.")

    df = pd.DataFrame(cleaned_records)
    
    df['raw_time'] = df['raw_time'].astype(str).str.replace(' ', ' ').str.replace('  ', ' ').str.strip()
    datetime_series = df['raw_date'] + ' ' + df['raw_time']
    
    df['timestamp'] = pd.to_datetime(datetime_series, format='mixed', errors='coerce')
    
    df = df.dropna(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    
    return df
