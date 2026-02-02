import smtplib
import os
import mimetypes
from email.message import EmailMessage

def send_mail_with_json(file_path: str):
    # 1. Load Config
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    
    # 2. Setup Message
    msg = EmailMessage()
    msg["Subject"] = "SceneSpot AI 🚨 JSON Data Export"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.set_content("Attached is the requested JSON index file for your review.")

    # 3. Read and Attach the File
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)
        
        # Add the attachment
        msg.add_attachment(
            file_data, 
            maintype='application', 
            subtype='json', 
            filename=file_name
        )
        print(f"📎 Attached: {file_name}")
    else:
        print(f"❌ Error: File not found at {file_path}")
        return

    # 4. Send
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, PASSWORD)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# --- HOW TO USE IT ---
# Call this function inside your process_video route, right after saving the file:
# send_mail_with_json("indices/my_video.json")