from dataclasses import dataclass
from datetime import datetime
from typing import Optional

EVENT_DESCRIPTIONS = {
    101: "SCI Fault",
    102: "EEPROM R/W Fault",
    103: "RLY-Check Fault",
    104: "DC INJ. High",
    105: "AUTO TEST FAILED",
    106: "High DC Bus",
    107: "Ref.Voltage Fault",
    108: "AC HCT Fault",
    109: "GFCI Fault",
    110: "Device Fault",
    111: "M-S version unmatched",
    112: "Reserve",
    132: "Reserve",
    133: "Fac Fault",
    134: "Vac Fault",
    135: "Utility Loss",
    136: "Ground fault",
    137: "PV Over voltage",
    138: "ISO Fault",
    139: "Reserve",
    140: "Over Temp.",
    141: "Vac differs for M-S",
    142: "Fac differs for M-S",
    143: "Groud I differs for M-S",
    144: "DC inj. differs for M-S",
    145: "Fac,Vac differs for M-S",
    146: "High DC Bus",
    147: "Consistent Fault",
    148: "Average volt of 10 minutes Fault",
    149: "Reserve",
    150: "Reserve",
    152: "Fuse Fault",
    153: "ISO check: before enable constant current，ISO voltage> 300mV",
    154: "ISO check: after enable constant current，ISO voltage out of range (1.37v +/- 20%)",
    155: "ISO check: N P relay change，ISO voltage sudden below 40mV",
    156: "GFCI protect fault :30mA lever",
    157: "GFCI protect fault :60mA lever",
    158: "GFCI protect fault :150mA lever",
    159: "PV1 string current abnormal",
    160: "PV2 string current abnormal",
    161: "DRED Communication Fails(S9 open)",
    162: "Operate the disconnection device(S0 close)",
}


@dataclass
class ZeverSolarEvent:
    event_time: datetime
    inverter_id: str
    event_code: int
    event_type: int

    @property
    def event_description(self) -> Optional[str]:
        return EVENT_DESCRIPTIONS.get(self.event_code, None)


__ALL__ = [ZeverSolarEvent]
