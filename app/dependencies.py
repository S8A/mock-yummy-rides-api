from enum import Enum

from fastapi import HTTPException, Header, Request
from fastapi.security import APIKeyHeader

from config import settings

class CustomAPIKeyHeader(APIKeyHeader):

    async def __call__(self, request: Request) -> str | None:
        api_key = await super().__call__(request)
        if api_key != settings.API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return api_key


api_key_header = CustomAPIKeyHeader(name="Api-Key", auto_error=True)


class Language(Enum):
    ES = "es"
    EN = "en"


def get_language_header(language: Language = Header(default=Language.ES)):
    return language
