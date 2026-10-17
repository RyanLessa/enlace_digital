from pydantic import BaseModel, ConfigDict


class Presenter(BaseModel):
    model_config = ConfigDict(from_attributes=True)
