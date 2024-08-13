import os
from fastapi.middleware.cors import CORSMiddleware
import traceback
import logging
from dotenv import load_dotenv
import logging.handlers
from fastapi import FastAPI, status, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from starlette.requests import Request
from starlette.responses import JSONResponse
from serializers import EmailDataSerializer
from models import db_engine, FormSubmissions
from sqlmodel import Session
from ip2geotools.databases.noncommercial import DbIpCity


load_dotenv()

email_config = ConnectionConfig(
   MAIL_USERNAME=os.getenv("SENDER_EMAIL"),
   MAIL_FROM=os.getenv("SENDER_EMAIL"),
   MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
   MAIL_PORT=int(os.getenv("MAIL_PORT")),
   MAIL_SERVER=os.getenv("MAIL_SERVER"),
   MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
   MAIL_STARTTLS = True,
   MAIL_SSL_TLS = False,
)
fastmail = FastMail(email_config)

logger = logging.getLogger()
logging.basicConfig(
   encoding='utf-8',
   level=int(os.getenv("LOGGING_LEVEL")),
   format='%(asctime)s %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p',
   handlers=[logging.handlers.TimedRotatingFileHandler(filename=os.getenv("LOG_FILE_PATH"), when="midnight")]
)

app = FastAPI()

ORIGINS = os.getenv("ORIGINS").split(", ")
app.add_middleware(
   CORSMiddleware,
   allow_origins=ORIGINS,
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"]
)

async def send_email_function(email_data):
   logger.info("Send email function called")

   replacements = {
      "{user_name}": email_data.name,
      "{user_email}": email_data.email,
      "{user_subject}": email_data.subject,
      "{user_message}": email_data.message
   }

   logger.debug(f"email_data: {email_data}")

   email_template = os.getenv("EMAIL_TEMPLATE")
   for key, value in replacements.items():
      email_template = email_template.replace(key, value)

   try:
      logger.info("Sending Email...")

      message = MessageSchema(
         subject=os.getenv("EMAIL_SUBJECT"),
         recipients=[os.getenv("RECEIVER_EMAIL")],
         body=email_template,
         subtype="html"
      )
      await fastmail.send_message(message)
      logger.info("Email sent successfully!")

   except Exception:
      logger.exception("Something went wrong:-")
      logger.exception(traceback.format_exc())
      

@app.post("/send-email")
async def send_email_api(request: Request, email_data: EmailDataSerializer, background_tasks: BackgroundTasks):
   logger.info("Send email API hit!")
   background_tasks.add_task(send_email_function, email_data)
   
   client_ip = request.client.host
   
   logger.info("Getting IP info...")
   response = DbIpCity.get(client_ip, api_key="free")
   
   logger.info("Saving the form entry to DB...")
   try:
      form = FormSubmissions(
         name = email_data.name,
         email = email_data.email,
         subject = email_data.subject,
         message = email_data.message,
         client_ip = client_ip,
         ip_city = response.city,
         ip_region = response.region,
         ip_country = response.country
      )

      with Session(db_engine) as session:  
         session.add(form)
         session.commit()
         
      logger.info("Form entry saved to DB successfully!")  
   
   except Exception:
      logger.exception("Something went wrong while saving to DB")
      logger.exception(traceback.format_exc())

   return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={"message": "Email Sent Successfully"}
   )
