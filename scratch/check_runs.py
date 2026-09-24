import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

token = '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'
owner = 'lookiq'
repo = 'jewelituse-1-Factify-YT-automation'

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json'
}

r = requests.get(f'https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=10', headers=headers)
runs = r.json().get('workflow_runs', [])
for run in runs:
    print(f"Run #{run['run_number']}: {run['name']} | Event: {run['event']} | Status: {run['status']} | Conclusion: {run['conclusion']} | Created: {run['created_at']}")
