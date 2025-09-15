import uvicorn
from fastapi import FastAPI

from app.config import API_PORT
from app.handlers.exceptions import APIException, api_exception_handler
from app.views.routes import resources, upload

description = """A REST API for JSON content with zero coding.

Technologies::
* Python 3.13
* FastAPI 0.116
"""
app = FastAPI(
    version="1.4.0",
    title="Yet Another JSON Server",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    contact={
        "name": "Adriano Vieira",
        "url": "https://www.adrianovieira.eng.br/",
    },
    description=description,
    openapi_tags=[{"name": "API"}],
)

app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(FileNotFoundError, api_exception_handler)
app.add_exception_handler(NotImplementedError, api_exception_handler)
app.add_exception_handler(Exception, api_exception_handler)

app.include_router(resources.router)
app.include_router(upload.router)


def main():
    uvicorn.run("app.api:app", host="0.0.0.0", port=API_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
