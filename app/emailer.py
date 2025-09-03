import smtplib, ssl, os
from email.message import EmailMessage

def send_mail(smtp_conf:dict, subject:str, body:str, attachments:list[str]):
    msg = EmailMessage()
    msg["From"] = smtp_conf["smtp_user"]
    msg["To"] = ", ".join(smtp_conf.get("smtp_recipients", []))
    msg["Subject"] = subject
    msg.set_content(body)

    for p in attachments:
        with open(p,"rb") as f:
            data = f.read()
        msg.add_attachment(data, maintype="application", subtype="pdf", filename=os.path.basename(p))

    if smtp_conf.get("smtp_ssl"):
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_conf["smtp_host"], smtp_conf["smtp_port"], context=ctx) as s:
            s.login(smtp_conf["smtp_user"], smtp_conf["smtp_pass_app"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(smtp_conf["smtp_host"], smtp_conf["smtp_port"]) as s:
            if smtp_conf.get("smtp_tls"): s.starttls()
            s.login(smtp_conf["smtp_user"], smtp_conf["smtp_pass_app"])
            s.send_message(msg)
