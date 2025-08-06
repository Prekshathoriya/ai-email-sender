import os
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq

# Load secrets from Streamlit secrets (or environment variables)
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL") or os.getenv("SENDER_EMAIL")
APP_PASSWORD = st.secrets.get("APP_PASSWORD") or os.getenv("APP_PASSWORD")

# Check keys loaded
if not GROQ_API_KEY:
    st.error("Groq API key is missing! Add it to Streamlit secrets or environment variables.")
    st.stop()

if not SENDER_EMAIL or not APP_PASSWORD:
    st.warning("Sender email or app password missing. You can enter these manually below.")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="AI Email Sender", layout="centered")
st.title("📧 AI-Generated Email Sender")

with st.form("email_form"):
    # Use secrets if available; else allow user input
    sender_email = SENDER_EMAIL or st.text_input("Your Gmail Address (sender)", placeholder="yourname@gmail.com")
    sender_password = APP_PASSWORD or st.text_input("Your Gmail App Password", type="password")
    recipient_emails = st.text_area("Recipient Email(s) (comma-separated)", placeholder="friend1@example.com, friend2@example.com")
    subject = st.text_input("Email Subject", placeholder="Quick catch-up")
    email_prompt = st.text_area("What should the email say?", placeholder="e.g. Apologize for delay and schedule a call this week")
    generate_clicked = st.form_submit_button("Generate Email")

    # Debug info after assignment
    st.write("Using email:", sender_email)
    st.write("Using app password:", (sender_password[:4] + "****") if sender_password else "No password yet")

# Store AI email content in session state
if 'ai_email_content' not in st.session_state:
    st.session_state.ai_email_content = ""

if generate_clicked:
    if not all([sender_email, sender_password, recipient_emails, subject, email_prompt]):
        st.error("Please fill in all fields.")
    else:
        with st.spinner("Generating email..."):
            try:
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert email writer. Keep emails friendly, clear, and professional."},
                        {"role": "user", "content": f"Write an email for this: {email_prompt}"}
                    ],
                    model="llama3-8b-8192"
                )
                ai_email_content = response.choices[0].message.content.strip()
                st.session_state.ai_email_content = ai_email_content
            except Exception as e:
                st.error(f"AI generation failed: {e}")

if st.session_state.ai_email_content:
    st.subheader("✉️ Generated Email (Editable)")
    edited_email = st.text_area("Edit your email here before sending:", value=st.session_state.ai_email_content, height=300)

    if st.button("Send Email"):
        if not all([sender_email, sender_password, recipient_emails, subject, edited_email]):
            st.error("Please fill in all fields to send the email.")
        else:
            try:
                msg = MIMEMultipart()
                msg["From"] = sender_email
                recipient_list = [email.strip() for email in recipient_emails.split(",") if email.strip()]
                msg["To"] = ", ".join(recipient_list)
                msg["Subject"] = subject
                msg.attach(MIMEText(edited_email, "plain"))

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipient_list, msg.as_string())

                st.success("✅ Email sent successfully!")
                st.session_state.ai_email_content = ""  # clear after send
            except smtplib.SMTPAuthenticationError:
                st.error("❌ Login failed. Make sure you use a valid Gmail **App Password**, not your normal password.")
            except Exception as e:
                st.error(f"❌ Failed to send email: {e}")
