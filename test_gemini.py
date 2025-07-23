import google.generativeai as genai

genai.configure(api_key="AIzaSyD0sCMbe7fcyx-cRVrX1DPwql-ppgoCuHg")

model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
# O prueba con: model = genai.GenerativeModel("models/gemini-2.5-pro")

try:
    response = model.generate_content("¿Cuál es la capital de Francia?")
    print("Respuesta de Gemini:", response.text)
except Exception as e:
    print("Error:", e)