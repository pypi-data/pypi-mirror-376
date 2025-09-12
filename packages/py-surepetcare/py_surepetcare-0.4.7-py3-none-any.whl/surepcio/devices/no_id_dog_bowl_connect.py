import logging
from typing import Any

from .device import BaseControl
from .device import BaseStatus
from .device import DeviceBase
from surepcio.command import Command
from surepcio.const import API_ENDPOINT_PRODUCTION
from surepcio.enums import ProductId

logger = logging.getLogger(__name__)


class NoIdDogBowlConnect(DeviceBase):
    def __init__(self, data: dict[Any, Any], **kwargs) -> None:
        try:
            super().__init__(data, **kwargs)
            self.status: BaseStatus = BaseStatus(**data)
            self.control: BaseControl = BaseControl(**data)
        except Exception as e:
            logger.warning("Error while storing data %s", data)
            raise e

    @property
    def product(self) -> ProductId:
        return ProductId.NO_ID_DOG_BOWL_CONNECT

    def refresh(self):
        def parse(response):
            if not response:
                return self
            self.status = BaseStatus(**{**self.status.model_dump(), **response["data"]})
            self.control = BaseControl(**{**self.control.model_dump(), **response["data"]})
            return self

        return Command(
            method="GET",
            endpoint=f"{API_ENDPOINT_PRODUCTION}/device/{self.id}",
            callback=parse,
        )
