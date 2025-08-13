import google.generativeai as genai

# Replace with your actual API key
API_KEY = "AIzaSyAG3OHH59pGnFpcnTHy-zPNeCOjOsl9NUo"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')

response = model.generate_content("Say hello and confirm you're working! also say what day is today , tell who are you?")
print(response.text)

