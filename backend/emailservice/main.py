import logging
import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


def send_in_background(
    sender_email, sender_password, receiver_email, email_subject, email_message
):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = email_subject
    message.attach(MIMEText(email_message, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
    except Exception as e:
        print(f"Error occurred while sending email: {e}")


@app.route("/v1/email", methods=["POST"])
def send_email() -> dict[str]:
    data = request.get_json()
    email_address = data["address"]
    email_subject = data["subject"]
    email_message = data["message"]

    sender_email = "jagacnoob2@gmail.com"
    sender_password = os.getenv("EMAIL_PASSWORD")
    receiver_email = email_address

    # Create a separate thread to send the email asynchronously
    email_thread = threading.Thread(
        target=send_in_background,
        args=(
            sender_email,
            sender_password,
            receiver_email,
            email_subject,
            email_message,
        ),
    )
    email_thread.start()

    return jsonify({"success": "Email request received and being processed."})
