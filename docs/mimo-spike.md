# Spike de MiMo — 30 minutos, bloqueante

**Dueño: Wilbert · antes de confiar en `ai/provider.py`**

La capa de IA ya está escrita, pero **la forma exacta de las partes de contenido
de audio e imagen está sin confirmar**: el dominio de la documentación de MiMo
estaba bloqueado cuando se escribió. Se implementó la convención de OpenAI, que
es lo que MiMo declara soportar, pero hay que verificarlo antes de construir
encima.

Corre los cuatro `curl`, pega la respuesta debajo de cada uno, y ajusta
`ai/provider.py` con lo que salga. Si el 4 falla, `ai/stt.py` se queda con los
audios sembrados y **el día no se bloquea**.

## Preparación

```bash
export MIMO_API_KEY="tu-llave"
# Si la llave es de Token Plan, la URL es regional: cópiala de la consola.
export MIMO_BASE_URL="https://api.xiaomimimo.com/v1"
```

## 1 · Texto simple — confirma URL, auth y nombre de modelo

```bash
curl -s "$MIMO_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $MIMO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mimo-v2.5-pro",
    "messages": [{"role":"user","content":"Responde solo: ok"}],
    "max_tokens": 20
  }' | python3 -m json.tool
```

**Qué buscar:** un `choices[0].message.content`. Si da 401, la llave o la URL
están mal. Si da 404 en el modelo, pedir la lista con
`curl -s "$MIMO_BASE_URL/models" -H "Authorization: Bearer $MIMO_API_KEY"`.

**Resultado:**

```
(pegar aquí)
```

## 2 · JSON mode — confirma `response_format`

```bash
curl -s "$MIMO_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $MIMO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mimo-v2.5-pro",
    "response_format": {"type": "json_object"},
    "messages": [{"role":"user","content":"Devuelve {\"horas\": 4520} y nada mas"}],
    "max_tokens": 60
  }' | python3 -m json.tool
```

**Qué buscar:** que el contenido sea JSON parseable sin envoltura. Recordá que
MiMo **no** fuerza el esquema, solo el formato — por eso `provider.chat_json`
valida con Pydantic y reintenta. No quites esa validación.

**Resultado:**

```
(pegar aquí)
```

## 3 · Imagen — confirma la forma de visión (para el OCR del horómetro)

```bash
# Cualquier imagen sirve para confirmar la forma de la petición.
IMG=$(curl -s "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Odometer_rollover.jpg/320px-Odometer_rollover.jpg" | base64 -w0)

curl -s "$MIMO_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $MIMO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"mimo-v2.5\",
    \"messages\": [{\"role\":\"user\",\"content\":[
      {\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/jpeg;base64,$IMG\"}},
      {\"type\":\"text\",\"text\":\"Que numeros se leen en la imagen?\"}
    ]}],
    \"max_tokens\": 120
  }" | python3 -m json.tool
```

**Qué buscar:** que describa números. Si rechaza `image_url`, probar
`{"type":"image","image":{"data":"<b64>"}}` y ajustar `chat_json` en
`provider.py` (la parte de contenido se arma en un solo lugar).

**Nota:** `mimo-v2.5` **no** acepta `response_format` — no se lo mandes.

**Resultado:**

```
(pegar aquí)
```

## 4 · Audio — la transcripción, que es el minuto 1 de la demo

```bash
# Grabá 5 segundos diciendo algo con jerga: "el horometro va en cuatro mil
# quinientas veinte". Un .ogg o .m4a del celular sirve.
AUD=$(base64 -w0 nota.ogg)

curl -s "$MIMO_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $MIMO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"mimo-v2.5\",
    \"messages\": [{\"role\":\"user\",\"content\":[
      {\"type\":\"input_audio\",\"input_audio\":{\"data\":\"$AUD\",\"format\":\"ogg\"}},
      {\"type\":\"text\",\"text\":\"Transcribe esta nota de voz literal, en espanol.\"}
    ]}],
    \"max_tokens\": 300
  }" | python3 -m json.tool
```

**Qué buscar:** la transcripción. Tres cosas a anotar:

1. ¿Acepta `ogg`/`opus`, o hay que convertir? WhatsApp manda **ogg/opus**.
   Si solo acepta `mp3` o `wav`, hace falta `ffmpeg -i in.ogg out.wav` en
   `ingest/whatsapp.py` al bajar el media.
2. ¿Entiende «horómetro» y los números dichos en palabras? El prompt de
   `ai/stt.py` ya le siembra el vocabulario técnico salvadoreño.
3. ¿Cuánto tarda? Si pasa de 15 s, el minuto 1 de la demo se siente lento y
   conviene precalentar con un audio de prueba antes de presentar.

**Resultado:**

```
(pegar aquí)
```

## Después del spike

```bash
# con IA real
MIMO_API_KEY=... ./scripts/smoke.sh
# sin llave: los respaldos tienen que dar el mismo resultado
MIMO_API_KEY= ./scripts/smoke.sh

./scripts/bitacora.sh "spike de MiMo: audio en <formato>, vision ok, ajustes en provider.py"
```

Las dos corridas importan igual. Los respaldos por reglas son la red de
seguridad contra el wifi del salón: si un cambio los rompe, el cambio está mal.
