import requests

url = "https://api.pdfrest.com/compressed-pdf"

payload = {
    
}

headers = {
    'Api-Key': 'e860d368-f53b-4561-be06-690f625f8045'
}

response = requests.post(url, headers=headers, data=payload)

print(response.text)