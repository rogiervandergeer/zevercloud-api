from datetime import datetime

from zevercloud.event import ZeverSolarEvent


def test_description():
    event = ZeverSolarEvent(event_time=datetime.now(), inverter_id="ZX1234", event_code=110, event_type=3)
    assert event.event_description == "Device Fault"
