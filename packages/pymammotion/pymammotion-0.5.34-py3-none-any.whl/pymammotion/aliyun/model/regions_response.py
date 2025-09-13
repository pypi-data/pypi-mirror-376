from dataclasses import dataclass
from typing import TypeVar

from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin

DataT = TypeVar("DataT")


@dataclass
class RegionResponseData(DataClassORJSONMixin):
    shortRegionId: str
    oaApiGatewayEndpoint: str
    regionId: str
    mqttEndpoint: str
    pushChannelEndpoint: str
    regionEnglishName: str
    apiGatewayEndpoint: str


@dataclass
class RegionResponse(DataClassORJSONMixin):
    data: RegionResponseData
    code: int
    id: str | None = None
    msg: str | None = None

    class Config(BaseConfig):
        omit_default = True
