import os
from sqlmodel import Field, SQLModel, create_engine
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv


load_dotenv()
local_tz = timezone("Asia/Kolkata")

db_engine = create_engine(os.getenv("DATABASE_URL"))

class FormSubmissions(SQLModel, table=True):
    __tablename__ = "form_submissions"
    
    id: int | None = Field(index=True, default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
    subject: str
    message: str
    sent_ts: datetime = Field(default=datetime.now(local_tz))
    client_ip: str = Field(index=True)
    ip_city: str
    ip_region: str
    ip_country: str
