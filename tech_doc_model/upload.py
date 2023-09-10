import requests

def upload_file_for_finetuning(file_path, api_key):
    url = "https://api.openai.com/v1/files"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f)}
        data = {'purpose': 'fine-tune'}
        
        response = requests.post(url, headers=headers, files=files, data=data)
        
    return response.json()

# Replace 'your_api_key_here' with your actual OpenAI API key
api_key = "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"

# Since the file is in the same directory as the script, just specify its name
file_path = "data.jsonl"

response = upload_file_for_finetuning(file_path, api_key)
print(response)
