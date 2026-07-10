from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    disabled: bool | None = None

class Session(BaseModel):
    session_id: str
    user: User
    is_active: bool = True

class Message(BaseModel):
    message_id: str
    session_id: str
    sender: str
    content: str
    timestamp: str

class Preset(BaseModel):
    preset_id: str
    name: str
    description: str | None = None
    model: str
    parameters: dict | None = None

class Userconfig(BaseModel):
    user_id: str
    preferences: dict | None = None
    last_login: str | None = None
