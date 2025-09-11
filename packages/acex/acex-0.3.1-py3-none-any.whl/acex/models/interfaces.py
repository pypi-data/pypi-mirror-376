from typing import Optional, Dict
from sqlmodel import SQLModel, Field

class Interface(SQLModel):
    name: str = Field(default="")


class PhysicalInterface(Interface):
    type: str = Field(default="")
    mac_address: Optional[str] = None
    speed_kbps: Optional[int] = None  # Speed in KBps
