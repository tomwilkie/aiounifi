"""Networks as part of a UniFi network."""

from dataclasses import dataclass
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequest


class TypedNetwork(TypedDict):
    """Network type definition."""

    _id: str
    attr_hidden_id: NotRequired[str]
    attr_no_delete: NotRequired[bool]
    enabled: NotRequired[bool]
    ip_subnet: NotRequired[str]
    name: NotRequired[str]
    purpose: NotRequired[str]
    site_id: NotRequired[str]
    vlan: NotRequired[int]
    vlan_enabled: NotRequired[bool]
    wan_dns_preference: NotRequired[str]
    wan_failover_priority: NotRequired[int]
    wan_load_balance_type: NotRequired[str]
    wan_load_balance_weight: NotRequired[int]
    wan_networkgroup: NotRequired[str]
    wan_type: NotRequired[str]


@dataclass
class NetworkListRequest(ApiRequest):
    """Request object for network list."""

    @classmethod
    def create(cls) -> Self:
        """Create network list request."""
        return cls(method="get", path="/rest/networkconf")


@dataclass
class NetworkUpdateRequest(ApiRequest):
    """Request object for network update."""

    @classmethod
    def create(cls, network: TypedNetwork) -> Self:
        """Create network update request.

        The controller rejects partial payloads, so the full network object
        has to be provided with the desired fields already modified.
        """
        return cls(
            method="put",
            path=f"/rest/networkconf/{network['_id']}",
            data=network,
        )


class Network(ApiItem):
    """Represent a network configuration."""

    raw: TypedNetwork

    @property
    def id(self) -> str:
        """ID of network."""
        return self.raw["_id"]

    @property
    def name(self) -> str | None:
        """Name of network."""
        return self.raw.get("name")

    @property
    def enabled(self) -> bool | None:
        """Is network enabled."""
        return self.raw.get("enabled")

    @property
    def purpose(self) -> str | None:
        """Purpose of network."""
        return self.raw.get("purpose")

    @property
    def is_wan(self) -> bool:
        """Is network a WAN."""
        return self.raw.get("purpose") == "wan"

    @property
    def wan_networkgroup(self) -> str | None:
        """WAN network group, such as WAN, WAN2 or WAN3."""
        return self.raw.get("wan_networkgroup")

    @property
    def wan_failover_priority(self) -> int | None:
        """WAN failover priority, lower value takes precedence."""
        return self.raw.get("wan_failover_priority")

    @property
    def wan_load_balance_type(self) -> str | None:
        """WAN load balance type, failover-only or weighted."""
        return self.raw.get("wan_load_balance_type")

    @property
    def wan_load_balance_weight(self) -> int | None:
        """WAN load balance weight."""
        return self.raw.get("wan_load_balance_weight")

    @property
    def wan_type(self) -> str | None:
        """WAN connection type."""
        return self.raw.get("wan_type")
