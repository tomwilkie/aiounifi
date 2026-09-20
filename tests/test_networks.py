"""Test network configuration API.

pytest --cov-report term-missing --cov=aiounifi.network tests/test_networks.py
"""

from copy import deepcopy

import pytest

from aiounifi.errors import AiounifiException
from aiounifi.models.network import NetworkListRequest, NetworkUpdateRequest

from .fixtures import NETWORKS

WAN1_ID = "678a1b2c3d4e5f6071829304"
WAN3_ID = "678a1b2c3d4e5f6071829306"
LAN_ID = "678a1b2c3d4e5f6071829307"


def test_network_list_request():
    """Test network list request."""
    request = NetworkListRequest.create()
    assert request.method == "get"
    assert request.path == "/rest/networkconf"


def test_network_update_request():
    """Test network update request carries the full object."""
    network = deepcopy(NETWORKS[0])
    network["wan_failover_priority"] = 3

    request = NetworkUpdateRequest.create(network)

    assert request.method == "put"
    assert request.path == f"/rest/networkconf/{WAN1_ID}"
    assert request.data == network


@pytest.mark.usefixtures("_mock_endpoints")
async def test_no_networks(unifi_controller, unifi_called_with):
    """Test that no networks also work."""
    networks = unifi_controller.networks
    await networks.update()

    assert unifi_called_with("get", "/api/s/default/rest/networkconf")
    assert len(networks.values()) == 0


@pytest.mark.parametrize("network_payload", [NETWORKS])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_networks(unifi_controller):
    """Test that different types of networks work."""
    networks = unifi_controller.networks
    await networks.update()
    assert len(networks.values()) == 4

    network = networks[WAN1_ID]
    assert network.id == WAN1_ID
    assert network.name == "Primary (WAN1)"
    assert network.enabled is True
    assert network.purpose == "wan"
    assert network.is_wan is True
    assert network.wan_networkgroup == "WAN"
    assert network.wan_failover_priority == 1
    assert network.wan_load_balance_type == "weighted"
    assert network.wan_load_balance_weight == 80
    assert network.wan_type == "dhcp"

    # A GRE based 5G WAN is missing many of the keys an ethernet WAN has.
    network = networks[WAN3_ID]
    assert network.is_wan is True
    assert network.wan_networkgroup == "WAN3"
    assert network.wan_failover_priority == 3
    assert network.wan_load_balance_type == "failover-only"
    assert network.wan_load_balance_weight is None
    assert network.wan_type is None

    network = networks[LAN_ID]
    assert network.purpose == "corporate"
    assert network.is_wan is False
    assert network.wan_networkgroup is None
    assert network.wan_failover_priority is None
    assert network.wan_load_balance_type is None


@pytest.mark.parametrize("network_payload", [NETWORKS])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_network_save(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test that a modified network can be written back."""
    networks = unifi_controller.networks
    await networks.update()

    network = deepcopy(networks[WAN1_ID].raw)
    network["wan_load_balance_weight"] = 60

    mock_aioresponse.put(
        f"https://host:8443/api/s/default/rest/networkconf/{WAN1_ID}",
        payload={"meta": {"rc": "ok"}, "data": [network]},
    )

    await networks.save(network)

    assert unifi_called_with(
        "put",
        f"/api/s/default/rest/networkconf/{WAN1_ID}",
        json=network,
    )
    assert networks[WAN1_ID].wan_load_balance_weight == 60


@pytest.mark.parametrize("network_payload", [NETWORKS])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_network_save_duplicate_failover_priority(
    mock_aioresponse, unifi_controller
):
    """Test that a rejected failover priority surfaces as an exception."""
    networks = unifi_controller.networks
    await networks.update()

    network = deepcopy(networks[WAN1_ID].raw)
    network["wan_failover_priority"] = 2

    mock_aioresponse.put(
        f"https://host:8443/api/s/default/rest/networkconf/{WAN1_ID}",
        payload={
            "meta": {"rc": "error", "msg": "api.err.WanFailOverPriorityAlreadyExists"}
        },
        status=400,
    )

    with pytest.raises(AiounifiException):
        await networks.save(network)

    assert networks[WAN1_ID].wan_failover_priority == 1


@pytest.mark.parametrize("network_payload", [NETWORKS])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_network_websocket_update(unifi_controller, new_ws_data_fn):
    """Test that a networkconf sync message updates the network."""
    networks = unifi_controller.networks
    await networks.update()

    network = deepcopy(NETWORKS[0])
    network["wan_failover_priority"] = 3

    new_ws_data_fn({"meta": {"message": "networkconf:sync"}, "data": [network]})

    assert networks[WAN1_ID].wan_failover_priority == 3
