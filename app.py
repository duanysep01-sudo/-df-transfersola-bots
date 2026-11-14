import os, json, base64, requests
from flask import Flask, request, jsonify
app = Flask(__name__)
TOKEN_WHATSAPP = os.environ.get("TOKEN_WHATSAPP")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

def leer_foto_con_ia(media_id):
    headers = {"Authorization": f"Bearer {TOKEN_WHATSAPP}"}
    info = requests.get(f"https://graph.facebook.com/v21.0/{media_id}", headers=headers).json()
    foto_bytes = requests.get(info["url"], headers=headers).content
    foto_b64 = base64.b64encode(foto_bytes).decode()
    url = "https://api.groq.com/openai/v1/chat/completions"
    hg = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "meta-llama/llama-4-scout-17b-16e-instruct","messages": [{"role": "user","content": [{"type": "text","text": "Lee esta factura de Republica Dominicana y devuelve SOLO JSON: {\"nombre\": \"\", \"rnc\": \"\", \"ncf\": \"\", \"subtotal\": 0, \"tipo\": \"Combustible, Repuesto, Peaje\"} Subtotal sin ITBIS, si solo hay total divide entre 1.18"},{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{foto_b64}"}}]}]}
    r = requests.post(url, headers=hg, json=payload).json()
    try:
        texto = r["choices"][0]["message"]["content"].replace("```json","").replace("```","").strip()
        return json.loads(texto)
    except:
        print(r)
        return None

def enviar_mensaje(to, texto):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN_WHATSAPP}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": texto}}
    requests.post(url, headers=headers, json=data)

@app.route("/", methods=["GET"])
def home():
    return "Bot DF TRANSFERSOLA activo"

@app.route("/webhook", methods=["GET"])
def verificar():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Error", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        de = msg["from"]
        if msg["type"] == "image":
            enviar_mensaje(de, "Recibida, estoy leyendo tu factura... ⏳")
            dato = leer_foto_con_ia(msg["image"]["id"])
            if dato:
                enviar_mensaje(de, f"✅ Listo:\nNombre: {dato['nombre']}\nRNC: {dato['rnc']}\nNCF: {dato['ncf']}\nSubtotal: {dato['subtotal']}\nTipo: {dato['tipo']}")
            else:
                enviar_mensaje(de, "No pude leerla, mándala más clara porfa")
        else:
            enviar_mensaje(de, "Mándame foto de la factura y te la leo 📸")
    except Exception as e:
        print(e)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
