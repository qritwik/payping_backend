import requests
import os

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY5Njc5MDBlNTg4ODRhNTI0ZjE2NmUwNSIsIm5hbWUiOiJQYXlQaW5nIiwiYXBwTmFtZSI6IkFpU2Vuc3kiLCJjbGllbnRJZCI6IjY5Njc5MDBlNTg4ODRhNTI0ZjE2NmUwMCIsImFjdGl2ZVBsYW4iOiJGUkVFX0ZPUkVWRVIiLCJpYXQiOjE3Njg2Mjc5MjZ9.PNTI5t4rSMB-pg3TNStYbZNJCgGeQokIEyBLljlwzBI"

URL = "https://backend.aisensy.com/campaign/t1/api/v2"

payload = {
    "apiKey": API_KEY,
    "campaignName": "payping_invoice_template_1",
    "destination": "918709996580",  # customer WhatsApp number
    "userName": "PayPing",
    "templateParams": [
        "Ritwik",            # var1
        "Ram Tutions",       # var2
        "#INV-5001",         # var3
        "5000",              # var4
        "25-12-2026",        # var5
        "ram@ybl",           # var6
        "8709996580"         # var7
    ],
    "source": "python"
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(URL, json=payload, headers=headers)

print("Status:", response.status_code)
print("Response:", response.json())
