"""Networks as part of a UniFi network."""

from ..models.api import TypedApiResponse
from ..models.message import MessageKey
from ..models.network import (
    Network,
    NetworkListRequest,
    NetworkUpdateRequest,
    TypedNetwork,
)
from .api_handlers import APIHandler


class Networks(APIHandler[Network]):
    """Represents network configurations."""

    obj_id_key = "_id"
    item_cls = Network
    process_messages = (MessageKey.NETWORK_CONF_UPDATED,)
    api_request = NetworkListRequest.create()

    async def save(self, network: TypedNetwork) -> TypedApiResponse:
        """Write a full network object back to the controller."""
        response = await self.controller.request(NetworkUpdateRequest.create(network))
        self.process_raw(response.get("data", []))
        return response
