import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailNotifier:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, recipient, subject, message):
        try:
            # Setup the MIME
            mime_message = MIMEMultipart()
            mime_message['From'] = self.username
            mime_message['To'] = recipient
            mime_message['Subject'] = subject

            # Add body to email
            mime_message.attach(MIMEText(message, 'plain'))

            # Connect and authenticate
            session = smtplib.SMTP(self.smtp_server, self.smtp_port)
            session.starttls()  # Secure the connection
            session.login(self.username, self.password)

            # Send email
            text = mime_message.as_string()
            session.sendmail(self.username, recipient, text)
            session.quit()

            print(f"Email sent successfully to {recipient}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

