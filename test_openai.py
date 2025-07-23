import openai

client = openai.OpenAI(api_key="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")

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "¿Cuál es la capital de Francia?"}
        ]
    )
    print("Respuesta de OpenAI:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
