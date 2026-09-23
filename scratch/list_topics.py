import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('pipeline/topics_database.json', 'r', encoding='utf-8') as f:
    topics = json.load(f)

for i, t in enumerate(topics):
    print(f"{i+1}. [{t.get('id')}] {t.get('title')} | Used: {t.get('used', False)}")
