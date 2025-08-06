import streamlit as st
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

# Load keys from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")

st.set_page_config(page_title="AI Email Sender", layout="centered")
st.title("📧 AI-Generated Email Sender")

recipient = st.text_input("Recipient Email (e.g. test@example.com)")
prompt = st.text_area("Enter your email prompt (e.g. 'Meeting Reminder')")

# Generate Email
if st.button("Generate Email"):
    if not prompt:
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Generating..."):
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}"
            }
            data = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are an email writing assistant."},
                    {"role": "user", "content": f"Write a professional email for: {prompt}"}
                ],
                "temperature": 0.7
            }

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)

            if response.status_code == 200:
                ai_email = response.json()['choices'][0]['message']['content']
                st.session_state.generated_email = ai_email
            else:
                st.error("AI generation failed. Check your API key.")

# Editable Text Area
if "generated_email" in st.session_state:
    edited_email = st.text_area("✍️ Edit Your Email Below", value=st.session_state.generated_email, height=300)

    if st.button("Send Email"):
        if not recipient or not edited_email:
            st.warning("Recipient and email body are required.")
        else:
            try:
                msg = EmailMessage()
                msg["Subject"] = "AI-Generated Email"
                msg["From"] = SENDER_EMAIL
                msg["To"] = recipient
                msg.set_content(edited_email)

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(SENDER_EMAIL, APP_PASSWORD)
                    smtp.send_message(msg)

                st.success("✅ Email sent successfully!")
            except Exception as e:
                st.error(f"❌ Failed to send email: {e}")
