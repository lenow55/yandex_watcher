import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


from pydantic import (
    Field,
    model_serializer
)

base_dir = "environment"

class Settings(BaseSettings):
    token: str = Field()  
    cloud_id: str = Field(alias='cloud-id')  
    folder_id: str = Field(alias='folder-id')  
    format: str = "json"

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(base_dir, 'yc.env'),
        )
    )

    @model_serializer(return_type=List)
    def ser_model(self) -> List:
        return ["--token", self.token,
                "--cloud-id", self.cloud_id,
                "--folder-id", self.folder_id,
                "--format", self.format]
