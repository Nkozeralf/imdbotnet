import requests
import os

# Configura tu token y tu chat ID aquí
TELEGRAM_TOKEN = "8138374226:AAFSE2UUVRbw8xoYcnLWrNYWub0nXdGV7Gc"
CHAT_ID = "833047329"  # Reemplaza con tu propio ID si cambia

def enviar_resumen_telegram(tienda, exitosos, fallidos):
    total = len(exitosos) + len(fallidos)
    msg = f"📦 *Resumen de pedidos para* `{tienda}`\n"
    msg += f"✅ Éxitos: {len(exitosos)}\n"
    msg += f"❌ Fallidos: {len(fallidos)}\n"
    msg += f"🔢 Total: {total}\n\n"

    if exitosos:
        msg += "*Últimos exitosos:*\n"
        for e in exitosos[-3:]:
            nombre = e.get("nombre", "-")
            order_id = e.get("order_id", "-")
            msg += f"🟢 `{nombre}` - ID {order_id}\n"
    
    if fallidos:
        msg += "\n*Últimos fallidos:*\n"
        for f in fallidos[-3:]:
            nombre = f.get("nombre", "-")
            motivo = f.get("mensaje", "Error")
            msg += f"🔴 `{nombre}` - {motivo[:40]}\n"

    # Enviar mensaje a Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[Telegram] ❌ Error enviando mensaje: {e}")
