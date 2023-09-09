import requests
import json

def start_fine_tuning_job(training_file_id, model, api_key):
    url = "https://api.openai.com/v1/fine_tuning/jobs"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "training_file": training_file_id,
        "model": model
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    return response.json()

# Replace 'your_api_key_here' with your actual OpenAI API key
api_key = "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"

# Replace 'your_training_file_id_here' with the ID of the file you've uploaded for training
training_file_id = "file-GyTBlkanTGRgfrzozvnTS01m"

# Specify the base model you wish to fine-tune
model = "gpt-3.5-turbo-0613"

response = start_fine_tuning_job(training_file_id, model, api_key)
print(response)
