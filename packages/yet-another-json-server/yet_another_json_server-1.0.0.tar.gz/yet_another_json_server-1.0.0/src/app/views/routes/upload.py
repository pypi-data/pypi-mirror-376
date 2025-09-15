from fastapi import APIRouter, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.config import API_DB_JSON_FILENAME
from app.controllers.upload import UploadController
from app.handlers.exceptions import ResponseHeaders

router = APIRouter()

upload_ctlr = UploadController()

description = """
Upload resources from a csv file.
    
Update resource if it exists or add it if it does not.
"""


@router.put(
    "/upload",
    summary=f"Update DB JSON file ({API_DB_JSON_FILENAME}) from CSV file content.",
    description=description,
    tags=["API"],
)
async def upload_json_file_from_csv(csv_file: UploadFile):
    response = await upload_ctlr.upload_db_json_from_csv(csv_file)
    return JSONResponse(
        content=jsonable_encoder(response),
        headers=ResponseHeaders.JSON_HEADERS.value,
        status_code=status.HTTP_200_OK,
    )
