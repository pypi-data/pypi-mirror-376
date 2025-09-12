import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Optional

from pydantic import Field

from surepcio.command import Command
from surepcio.devices.entities import BaseControl
from surepcio.devices.entities import BaseStatus
from surepcio.devices.entities import EntityInfo
from surepcio.entities.battery_mixin import BatteryMixin
from surepcio.enums import ProductId

logger = logging.getLogger(__name__)


class SurePetCareBase(ABC):
    entity_info: EntityInfo = Field(default_factory=EntityInfo)
    status: BaseStatus = Field(default_factory=BaseStatus)
    control: BaseControl = Field(default_factory=BaseControl)

    def __init__(self, data: dict, timezone=None, **kwargs) -> None:
        self.entity_info = EntityInfo(**{**data, "product_id": self.product_id})
        self.timezone = timezone

    @property
    @abstractmethod
    def product(self) -> ProductId:
        raise NotImplementedError("Subclasses must implement product_id")

    @property
    def product_id(self) -> int:
        return self.product.value

    @property
    def product_name(self) -> str:
        return self.product.name

    def __str__(self):
        return f"<{self.__class__.__name__} id={self.id}>"

    def refresh(self) -> Command:
        """Refresh the device data."""
        raise NotImplementedError("Subclasses must implement refresh method")


class DeviceBase(SurePetCareBase, BatteryMixin):
    def __init__(self, data: dict[Any, Any], **kwargs):
        super().__init__(data, **kwargs)

    @property
    def parent_device_id(self) -> Optional[int]:
        return self.entity_info.parent_device_id

    @property
    def available(self) -> Optional[bool]:
        return self.status.online if self.status is not None else None

    @property
    def photo(self) -> str | None:
        """Return the url path for device photo."""
        return None

    @property
    def id(self) -> Optional[int]:
        return self.entity_info.id

    @property
    def household_id(self) -> int:
        if self.entity_info.household_id is None:
            raise ValueError("household_id is not set")
        return self.entity_info.household_id

    @property
    def name(self) -> str:
        return self.entity_info.name


class PetBase(SurePetCareBase):
    def __init__(self, data: dict[Any, Any], **kwargs):
        super().__init__(data, **kwargs)

    @property
    def available(self) -> Optional[bool]:
        return self.status.online

    @property
    def photo(self) -> str | None:
        """Return the url path for device photo."""
        return None

    @property
    def id(self) -> Optional[int]:
        return self.entity_info.id

    @property
    def household_id(self) -> int:
        return self.entity_info.household_id

    @property
    def name(self) -> str:
        return self.entity_info.name
