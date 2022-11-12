import smtplib
from email.message import EmailMessage

class Email:
    def __init__(self):
        self.msg = EmailMessage()
        
    def add_attachment(self, file_path):
        with open(file_path,"rb") as f:
            data = f.read()
            file_name = (f.name).split("/")[-1]
            self.msg.add_attachment(data, maintype="application", subtype="xlsx", filename=file_name)
          
    def send_email(self, subject, user_name, to, password, file_path, content=None):
        self.set_content(subject, user_name, to, content=content)
        self.add_attachment(file_path)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(user_name, password)
            server.send_message(self.msg)
   
    def set_content(self, subject, user_name, to, content=None):
        self.msg["Subject"] = subject
        self.msg["From"] = user_name
        self.msg["To"] = to
        if content:
            self.msg.set_content(content)
