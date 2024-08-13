from pydantic import BaseModel, EmailStr


class EmailDataSerializer(BaseModel):
    email: EmailStr
    message: str
    name: str
    subject: str
