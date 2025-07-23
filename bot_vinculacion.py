from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

# Configura tu token de bot y la URL de tu API
import os
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')  # Ahora el token se toma de la variable de entorno
'8098388898:AAFBQN4AGi4ki66E8GgGl63iAV60aXDlFcg'
API_URL = os.environ.get('DJANGO_API_URL', 'http://localhost:8000/api/vincular-telegram/')

# Carga el modelo conversacional de Hugging Face (GPT-2 español)
MODEL_NAME = "datificate/gpt2-small-spanish"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

def obtener_respuesta_ia(mensaje_usuario):
    prompt = f"Usuario: {mensaje_usuario}\nIA: "
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    outputs = model.generate(inputs, max_new_tokens=60, pad_token_id=tokenizer.eos_token_id)
    respuesta = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extrae solo la parte de la IA
    partes = respuesta.split("IA:")
    if len(partes) > 1:
        respuesta_ia = partes[-1].strip()
    else:
        respuesta_ia = respuesta.strip()
    # Elimina repeticiones vacías o respuestas poco útiles
    if not respuesta_ia or respuesta_ia.lower() in ["", "ia", "jo:"] or respuesta_ia.startswith("JO:"):
        respuesta_ia = "Lo siento, no entendí la pregunta. ¿Puedes reformularla?"
    print(f"[DEBUG] Respuesta generada: {respuesta_ia}")
    return respuesta_ia

ASK_EMAIL, ASK_PASS = range(2)
user_data = {}

# Diccionario de preguntas frecuentes
FAQ = {
    "¿cómo vinculo mi cuenta?": "Para vincular tu cuenta, usa el comando /start y sigue las instrucciones para ingresar tu correo y contraseña.",
    "¿qué servicios ofrecen?": "Ofrecemos mantenimiento preventivo, correctivo, diagnóstico, alineación, balanceo y más. ¡Pregunta por tu servicio!",
    "¿cómo contacto al taller?": "Puedes contactarnos al teléfono 555-123-4567 o por este chat de Telegram.",
    "¿cuándo es mi próximo mantenimiento?": "Puedes consultar tu próximo mantenimiento en la app web o escribirnos aquí para más detalles.",
}

def buscar_faq(pregunta):
    pregunta = pregunta.lower().strip()
    for key in FAQ:
        if key in pregunta:
            return FAQ[key]
    return None

from telegram.ext import CommandHandler
import asyncio

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "Preguntas frecuentes:\n"
    for i, q in enumerate(FAQ.keys(), 1):
        texto += f"{i}. {q.capitalize()}\n"
    texto += "\nEscribe la pregunta exacta o usa /ia para otras dudas."
    await update.message.reply_text(texto)

async def ia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = ' '.join(context.args)
    if not pregunta:
        await update.message.reply_text("Por favor, escribe tu pregunta después de /ia")
        return
    # Primero intenta responder con FAQ
    respuesta_faq = buscar_faq(pregunta)
    if respuesta_faq:
        await update.message.reply_text(respuesta_faq)
        return
    await update.message.reply_text("Pensando... (esto puede tardar unos segundos la primera vez)")
    loop = asyncio.get_running_loop()
    respuesta = await loop.run_in_executor(None, obtener_respuesta_ia, pregunta)
    await update.message.reply_text(respuesta)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Por favor, ingresa tu correo electrónico registrado en la app.")
    return ASK_EMAIL

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id] = {'correo': update.message.text}
    await update.message.reply_text("Ahora ingresa tu contraseña:")
    return ASK_PASS

async def ask_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    correo = user_data[chat_id]['correo']
    password = update.message.text
    # Llama a la API para vincular
    try:
        resp = requests.post(API_URL, json={'correo': correo, 'password': password, 'chat_id': str(chat_id)}, timeout=10)
        data = resp.json()
        if resp.ok and data.get('ok'):
            await update.message.reply_text("✅ ¡Vinculación exitosa! Ahora recibirás notificaciones aquí.")
        else:
            await update.message.reply_text(f"❌ Error: {data.get('error', 'Desconocido')}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error de conexión con el servidor: {e}")
    return ConversationHandler.END

from telegram.ext import CommandHandler

import asyncio

async def ia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = ' '.join(context.args)
    if not pregunta:
        await update.message.reply_text("Por favor, escribe tu pregunta después de /ia")
        return
    await update.message.reply_text("Pensando... (esto puede tardar unos segundos la primera vez)")
    loop = asyncio.get_running_loop()
    respuesta = await loop.run_in_executor(None, obtener_respuesta_ia, pregunta)
    await update.message.reply_text(respuesta)


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_pass)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
    # Agrega el comando /ia
    app.add_handler(CommandHandler("ia", ia_command))
    app.add_handler(CommandHandler("faq", faq_command))
    print("Bot corriendo. ¡Envíale /start o /ia o /faq en Telegram!")
    app.run_polling()

if __name__ == '__main__':
    main()
