from app.config import API_DB_JSON_FILENAME
from app.handlers.commons import convert_csv_bytes_to_json, to_kebabCase
from app.models.db_json_content import JsonContentModel


class UploadController:
    def __init__(self):
        self.json_content_mdl: JsonContentModel = JsonContentModel()

    async def upload_db_json_from_csv(self, csv_file):
        resource_name = csv_file.filename
        csv_data_bytes = await csv_file.read()
        await csv_file.close()

        resource_name = resource_name[:-4] if ".csv" in resource_name else resource_name
        resource_name = " ".join(resource_name.split("_"))
        resource_name = to_kebabCase(resource_name)

        obj_json: list[dict] = convert_csv_bytes_to_json(csv_data_bytes)

        self.json_content_mdl.update_db_json_content(resource_name, obj_json)

        return {
            "message": "Updated DB JSON ({}) from the {} content.".format(
                API_DB_JSON_FILENAME, csv_file.filename
            ),
            f"{resource_name}": obj_json[:5],
        }
