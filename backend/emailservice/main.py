import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/v1/email", methods=["POST"])
def send():
    email_address = request.form["address"]
    email_subject = request.form["subject"]
    email_message = request.form["message"]

    sender_email = ""
    sender_password = ""
    receiver_email = email_address

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

        return jsonify({"message": "email sent"})
    except Exception as e:
        return str(e)
