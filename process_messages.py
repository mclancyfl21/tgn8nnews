import json
import re
from datetime import datetime
from typing import List, Dict, Optional

def remove_emojis(text: str) -> str:
    """Remove emojis and other special Unicode characters."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FAFF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def clean_text(text: str) -> str:
    """Clean message text: remove emojis, links, excessive whitespace."""
    # Remove emojis
    text = remove_emojis(text)
    
    # Remove Telegram links and channel references
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Markdown links
    text = re.sub(r'https?://\S+', '', text)    # URLs
    text = re.sub(r't\.me/\S+', '', text)        # Telegram links
    
    # Remove excessive dashes and separators
    text = re.sub(r'-{3,}', '', text)
    text = re.sub(r'={3,}', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def contains_excluded_content(text: str) -> bool:
    """Check if message contains Israel/Gaza/Iran related content."""
    excluded_terms = [
        'israel', 'israeli', 'idf', 'gaza', 'hamas', 'iran', 'iranian',
        'tel aviv', 'tehran', 'netanyahu', 'hezbollah', 'palestine',
        'palestinian', 'west bank', 'jerusalem'
    ]
    
    text_lower = text.lower()
    return any(term in text_lower for term in excluded_terms)

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp from message format [YYYY-MM-DD HH:MM:SS]."""
    match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', timestamp_str)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
    return None

def extract_messages(news_content: str) -> List[Dict]:
    """Extract individual messages from the news content."""
    messages = []
    
    # Split by group sections
    group_sections = re.split(r'\*\*Group: (.+?)\*\*', news_content)
    
    current_group = "Unknown"
    for i in range(1, len(group_sections), 2):
        if i + 1 < len(group_sections):
            current_group = group_sections[i].strip()
            group_content = group_sections[i + 1]
            
            # Split by separator lines
            message_blocks = re.split(r'-{70,}', group_content)
            
            for block in message_blocks:
                block = block.strip()
                if not block or len(block) < 50:
                    continue
                
                # Extract timestamp
                timestamp = parse_timestamp(block)
                
                # Clean the message text
                cleaned_text = clean_text(block)
                
                # Skip if excluded content
                if contains_excluded_content(cleaned_text):
                    continue
                
                # Skip promotional/boilerplate content
                if any(phrase in cleaned_text.lower() for phrase in 
                       ['subscribe', 'donate', 'follow us', 'join us', 'advertising']):
                    continue
                
                if cleaned_text and len(cleaned_text) > 100:
                    messages.append({
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'group': current_group,
                        'text': cleaned_text,
                        'original_length': len(block)
                    })
    
    return messages

def calculate_time_window(messages: List[Dict]) -> Dict[str, str]:
    """Calculate the exact time window covered by messages."""
    timestamps = [
        datetime.fromisoformat(msg['timestamp']) 
        for msg in messages 
        if msg['timestamp']
    ]
    
    if not timestamps:
        return {'start': 'Unknown', 'end': 'Unknown'}
    
    start_time = min(timestamps)
    end_time = max(timestamps)
    
    return {
        'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_hours': round((end_time - start_time).total_seconds() / 3600, 2)
    }

def preprocess_messages(input_file: str = 'messages.json', 
                       output_file: str = 'messages_processed.json'):
    """Main preprocessing function."""
    
    print(f"Loading data from {input_file}...")
    
    # Load the raw data
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Debug: Print structure
    print(f"Raw data type: {type(raw_data)}")
    if isinstance(raw_data, list):
        print(f"List length: {len(raw_data)}")
        if len(raw_data) > 0:
            print(f"First element keys: {raw_data[0].keys() if isinstance(raw_data[0], dict) else 'Not a dict'}")
    elif isinstance(raw_data, dict):
        print(f"Dictionary keys: {raw_data.keys()}")
    
    # Try to extract the news content - handle different structures
    news_content = None
    
    try:
        # Try structure 1: Direct dictionary with result key
        if isinstance(raw_data, dict) and 'result' in raw_data:
            body = raw_data.get('result', {}).get('body')
            if body:
                body_data = json.loads(body) if isinstance(body, str) else body
                news_content = body_data.get('news_content')
    except Exception as e:
        print(f"Structure 1 failed: {e}")
    
    if not news_content:
        try:
            # Try structure 2: List with Lambda response
            if isinstance(raw_data, list) and len(raw_data) > 0:
                body = raw_data[0].get('result', {}).get('body')
                if body:
                    body_data = json.loads(body) if isinstance(body, str) else body
                    news_content = body_data.get('news_content')
        except Exception as e:
            print(f"Structure 2 failed: {e}")
    
    if not news_content:
        try:
            # Try structure 3: Direct dictionary with news_content
            if isinstance(raw_data, dict):
                news_content = raw_data.get('news_content')
        except Exception as e:
            print(f"Structure 3 failed: {e}")
    
    if not news_content:
        print("\nERROR: Could not extract news_content from the file.")
        print("Please check the file structure.")
        
        # Try to show what we have
        if isinstance(raw_data, str):
            print(f"\nFirst 500 chars of content:\n{raw_data[:500]}")
        else:
            print(f"\nFirst element:\n{json.dumps(raw_data[0] if isinstance(raw_data, list) else raw_data, indent=2)[:1000]}")
        return
    
    print(f"Successfully extracted news content ({len(news_content)} characters)")
    
    print("Extracting and cleaning messages...")
    messages = extract_messages(news_content)
    
    # Sort by timestamp
    messages.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '')
    
    # Calculate time window
    time_window = calculate_time_window(messages)
    
    # Prepare output
    output_data = {
        'metadata': {
            'total_messages': len(messages),
            'time_window': time_window,
            'processed_at': datetime.now().isoformat()
        },
        'messages': messages
    }
    
    # Save processed data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessing complete!")
    print(f"Total messages extracted: {len(messages)}")
    print(f"Time window: {time_window['start']} to {time_window['end']}")
    print(f"Duration: {time_window['duration_hours']} hours")
    print(f"Output saved to: {output_file}")
    
    # Print sample statistics
    groups = {}
    for msg in messages:
        groups[msg['group']] = groups.get(msg['group'], 0) + 1
    
    print(f"\nMessages by group:")
    for group, count in sorted(groups.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {group}: {count}")

if __name__ == "__main__":
    preprocess_messages()
