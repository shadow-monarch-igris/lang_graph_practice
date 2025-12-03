import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from twilio.rest import Client
import os
import json
import re

# ----------------------------------------
# LOAD ENV VARS
# ----------------------------------------
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("gen_api")     # Gemini API Key
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")

# ----------------------------------------
# INIT LLM (Gemini)
# ----------------------------------------
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# ----------------------------------------
# TWILIO CONFIG
# ----------------------------------------
WHATSAPP_NUMBER = "whatsapp:+14155238886"   # Twilio Sandbox
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# ----------------------------------------
# CLEAN JSON OUTPUT
# ----------------------------------------
def clean_json_output(raw: str) -> str:
    raw = raw.strip()

    # Remove markdown code blocks like ```json ... ```
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9]*", "", raw.strip())   # remove ```json
        raw = re.sub(r"```$", "", raw.strip())               # remove ending ```
    
    # Extract only the JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return match.group(0).strip()
    
    return raw


# ----------------------------------------
# GENERATE MESSAGE USING GEMINI
# ----------------------------------------
def generate_message(prompt):
    full_prompt = f"""
You are an assistant that outputs ONLY valid JSON.

IMPORTANT RULES:
- Output MUST be valid JSON.
- DO NOT use markdown.
- DO NOT use backticks like ```json.
- DO NOT add extra text outside JSON.
- Only output pure JSON.

JSON Format:
{{
  "title": "",
  "body": "",
  "call_to_action": "",
  "footer": ""
}}

Tone Rules:
- Hinglish
- Short, clean, professional

User Input: {prompt}
"""

    response = model.invoke(full_prompt)
    cleaned = clean_json_output(response.content)
    return cleaned


# ----------------------------------------
# SEND MESSAGE VIA TWILIO WHATSAPP
# ----------------------------------------
def send_whatsapp(to_number, message):
    msg = twilio_client.messages.create(
        body=message,
        from_=WHATSAPP_NUMBER,
        to=f"whatsapp:{to_number}"
    )
    return msg.sid


# ----------------------------------------
# STREAMLIT UI
# ----------------------------------------
st.title("📩 AI WhatsApp Message Generator (Gemini + Twilio)")

prompt = st.text_area("Enter message instruction:", height=140)
number = st.text_input("Client WhatsApp Number:", placeholder="+91XXXXXXXXXX")

if st.button("Generate Message"):
    if not prompt.strip():
        st.error("Please enter a prompt!")
    else:
        with st.spinner("Generating with Gemini..."):
            structured_json = generate_message(prompt)

        st.subheader("Raw Model Output")
        st.code(structured_json)

        # Parse JSON safely
        try:
            msg = json.loads(structured_json)
            final_message = (
                f"{msg['title']}\n\n"
                f"{msg['body']}\n\n"
                f"{msg['call_to_action']}\n\n"
                f"{msg['footer']}"
            )

            st.subheader("Final WhatsApp Message")
            st.text(final_message)

            st.session_state["final_message"] = final_message

        except Exception as e:
            st.error(f"❌ Invalid JSON returned\nError: {e}")

if st.button("Send to WhatsApp"):
    if "final_message" not in st.session_state:
        st.error("Please generate a message first!")
    elif not number.strip():
        st.error("Please enter WhatsApp number!")
    else:
        with st.spinner("Sending message via Twilio..."):
            sid = send_whatsapp(number, st.session_state["final_message"])
        st.success(f"Message sent successfully! SID: {sid}")
                        
