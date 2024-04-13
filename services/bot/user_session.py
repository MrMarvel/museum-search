import asyncio
from dataclasses import dataclass, field
from typing import Callable
@dataclass
class UserSession:
    chat_id:str|None=None
    loop: asyncio.BaseEventLoop | None = None
    callback:Callable=field(default_factory=lambda *args, **kwargs: None)