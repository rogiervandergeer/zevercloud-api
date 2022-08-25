from base64 import b64encode
from datetime import datetime, date, time, timedelta
from hashlib import sha256
from hmac import new as hmac
from typing import Any, Dict, List, Union

from requests import get

from zevercloud.event import ZeverSolarEvent


class ZeverCloud:
    """
    Python wrapper for the ZeverCloud API

    Args:
        api_key (str): Your api key.
            Can be found on the Zevercloud site, under `Configuration > Plant Configuration > 5. Api Key`.
        app_key (str): Your app key.
            Can be found under `Account Management > Security Settings`.
        app_secret (str): Your app secret.
            Can be found under `Account Management > Security Settings`.

    Note that the app_key and app_secret are only visible once approved by Zeversolar Support.
    Send an email to service.eu@zeversolar.net, for example, and ask them to make the `app_key`
    and `app_secret` visible to you.
    """

    def __init__(self, api_key: str, app_key: str, app_secret: str):
        self.api_key = api_key
        self.app_key = app_key
        self.app_secret = app_secret

    @property
    def overview(self) -> Dict[str, Any]:
        """
        Retrieve an overview of the current status of the site.

        Returns a dictionary like:
        {
            "last_updated": datetime(2022, 2, 3, 13, 57, 26),
            "online": False,
            "power": 0,
            "site_id": 12345,
            "yield": {
                "today": 5.9,
                "month": 218.42,
                "total": 5800,
                "year": 1770,
            },
        }
        """
        result = self._get(f"/getPlantOverview?key={self.api_key}")
        return {
            "last_updated": datetime.strptime(result["ludt"], "%Y-%m-%d %H:%M:%S"),
            "online": result["status"] == 1,
            "power": self._apply_unit(**result["Power"]),
            "site_id": result["sid"],
            "yield": {
                "today": self._apply_unit(**result["E-Today"]),
                "month": self._apply_unit(**result["E-Month"]),
                "year": self._apply_unit(**result["E-Year"]),
                "total": self._apply_unit(**result["E-Total"]),
            },
        }

    def get_events(self, start_date: date, end_date: date) -> List[ZeverSolarEvent]:
        """
        Get a list of events -errors- that occurred between start_date and end_date.

        Note that the API can only return events for 7 days at a time. Using this method
        on a large date range will result in many API-calls being made, and may hence
        take a rather long time.

        Args:
            start_date (date): The start date (inclusive)
            end_date (date): The end date (inclusive)
        """
        result = []
        while (end_date - start_date).days > 6:
            result += self._get_events(start_date, start_date + timedelta(days=6))
            start_date = start_date + timedelta(days=7)
        result += self._get_events(start_date, end_date)
        return result

    def get_output(self, date: date) -> List[Dict[str, Union[int, datetime]]]:
        """
        Get the power output of the site at 20-minute intervals on the provided date.

        Returns a list of dictionaries of the form:
        [
           ...
            {"power": 1183, "timestamp": datetime(2022, 8, 1, 12, 0)},
            {"power": 1240, "timestamp": datetime(2022, 8, 1, 12, 20)},
            {"power": 1815, "timestamp": datetime(2022, 8, 1, 12, 40)},
            ...
        ]

        The unit of the power field is Watt.

        Args:
            date (date): The date for which to request the power data.
        """
        response = self._get(f"/getPlantOutput?date={date.strftime('%Y-%m-%d')}&key={self.api_key}&period=bydays")
        return [
            dict(
                timestamp=datetime.combine(
                    date=date,
                    time=time(hour=int(entry["time"][:2]), minute=int(entry["time"][-2:])),
                ),
                power=self._apply_unit(value=float(entry["value"]), unit=response["dataunit"]),
            )
            for entry in response["data"]
        ]

    def get_details(self, date: date, psno: str) -> List[Dict[str, Union[datetime, int, float, str]]]:
        """
        Get monitor details at 10-minutes on the provided date.

        Returns a list of dictionaries of the form:
        [
           {
            'ac_frequency': 50,
            'ac_power': 30,
            'ac_current_p1': 0,
            'ac_current_p2': 0,
            'ac_current_p3': 0,
            'ac_voltage_p1': 236.8,
            'ac_voltage_p2': 0,
            'ac_voltage_p3': 0,
            'inverter_id': 'ZS12345678',
            'pv_current_1': 0,
            'pv_current_2': 0,
            'pv_current_3': 0,
            'pv_voltage_1': 271.4,
            'pv_voltage_2': 0,
            'pv_voltage_3': 0,
            'temperature': 26.7,
            'timestamp': datetime.datetime(2022, 8, 1, 6, 49, 37),
            'yield_today': 0.1,
            'yield_total': 5615.2
           }
        ]

        Args:
            date (date): The date for which to request the data.
            psno (str): The ID of the monitor. E.g. EAB1234C5678.
        """
        response = self._get(f"/getpmudata?apikey={self.api_key}&date={date.strftime('%Y-%m-%d')}&psno={psno}")
        return [
            dict(
                ac_frequency=entry.get("fac"),
                ac_power=entry.get("pac"),
                ac_current_p1=entry.get("iac1"),
                ac_current_p2=entry.get("iac2"),
                ac_current_p3=entry.get("iac3"),
                ac_voltage_p1=entry.get("vac1"),
                ac_voltage_p2=entry.get("vac2"),
                ac_voltage_p3=entry.get("vac3"),
                inverter_id=entry.get("isno"),
                pv_current_1=entry.get("ipv1"),
                pv_current_2=entry.get("ipv2"),
                pv_current_3=entry.get("ipv3"),
                pv_voltage_1=entry.get("vpv1"),
                pv_voltage_2=entry.get("vpv2"),
                pv_voltage_3=entry.get("vpv3"),
                temperature=entry.get("tempval"),
                timestamp=datetime.strptime(entry["recvdate"], "%Y-%m-%d %H:%M:%S"),
                yield_today=entry.get("e_today"),
                yield_total=entry.get("e_total"),
            )
            for entry in response["data"]
        ]

    def get_daily_output(self, month: date) -> List[Dict[str, Any]]:
        """
        Get the daily yield of the site in the given month.

        Returns a list of dictionaries of the form:
        [
            {"date": date(2022, 3, 1), "yield": 4.1},
            {"date": date(2022, 8, 2), "yield": 5.2},
            {"date": date(2022, 8, 3), "yield": 0.2},
            ...
        ]

        The unit of the yield field is kWh.

        Args:
            month (date): The month for which to request yield data.
                Accepts a datetime.date object, of which the day field is ignored.
        """
        response = self._get(f"/getPlantOutput?date={month.strftime('%Y-%m')}&key={self.api_key}&period=bymonth")
        return [
            {
                "date": datetime.strptime(entry["time"], "%Y-%m-%d").date(),
                "yield": self._apply_unit(value=float(entry["value"]), unit=response["dataunit"]),
            }
            for entry in response["data"]
        ]

    def get_monthly_output(self, year: int) -> List[Dict[str, Any]]:
        """
        Get the monthly yield of the site in the given year.

        Returns a list of dictionaries of the form:
        [
           {"date": date(2022, 1, 1), "yield": 40.1},
           {"date": date(2022, 2, 1), "yield": 52.1},
           {"date": date(2022, 3, 1), "yield": 113},
           {"date": date(2022, 4, 1), "yield": 8.11},
            ...
        ]

        The unit of the yield field is kWh.

        Args:
            year (int): The year for which to request yield data.
        """
        if not isinstance(year, int) or len(str(year)) != 4:
            raise ValueError(f"Year must be a four-digit integer. Got {year}.")
        response = self._get(f"/getPlantOutput?date={year}&key={self.api_key}&period=byyear")
        return [
            {
                "date": datetime.strptime(entry["time"] + "-01", "%Y-%m-%d").date(),
                "yield": self._apply_unit(value=float(entry["value"]), unit=response["dataunit"]),
            }
            for entry in response["data"]
        ]

    def get_yearly_output(self) -> List[Dict[str, Any]]:
        """
        Get the yearly yield of the site in its entire existence.

        Returns a list of dictionaries of the form:
        [
           {"year": 2012, "yield": 4069},
           {"year": 2013, "yield": 308},
            ...
        ]

        The unit of the yield field is kWh.
        """
        response = self._get(f"/getPlantOutput?key={self.api_key}&period=bytotal")
        return [
            {
                "year": int(entry["time"]),
                "yield": self._apply_unit(value=float(entry["value"]), unit=response["dataunit"]),
            }
            for entry in response["data"]
        ]

    def _get_events(self, start_date: date, end_date: date) -> List[ZeverSolarEvent]:
        """
        Get a list of events that occurred between start_date and end_date.

        The start and end date may not be more than six days apart.
        """
        if (end_date - start_date).days > 6:
            raise ValueError("Can not request more than 7 days of events at once.")
        result = self._get(
            f"/getPlantEvent?edt={end_date.strftime('%Y-%m-%d')}"
            f"&key={self.api_key}&sdt={start_date.strftime('%Y-%m-%d')}"
        )
        if result.get("code") == 0:
            return []  # No events in time range.
        return [
            ZeverSolarEvent(
                event_time=datetime.strptime(entry["eventTime"], "%Y-%m-%d %H:%M:%S"),
                event_type=int(entry["eventType"]),
                event_code=int(entry["eventCode"]),
                inverter_id=entry["ssno"],
            )
            for entry in result["data"]
        ]

    def _get(self, url: str) -> Dict[str, Any]:
        # TODO: rate limiting
        headers_to_sign = {"X-Ca-Key": self.app_key}
        headers_string = "".join([f"{key}:{headers_to_sign[key]}\n" for key in sorted(headers_to_sign.keys())])
        payload = f"GET\napplication/json\n\n\n\n{headers_string}{url}"
        signature = hmac(
            key=self.app_secret.encode("UTF-8"),
            digestmod=sha256,
            msg=payload.encode("UTF-8"),
        ).digest()
        headers = {
            "X-Ca-Signature-Headers": ",".join(headers_to_sign.keys()),
            "X-Ca-Signature": b64encode(signature).decode("UTF-8"),
            "Accept": "application/json",
            **headers_to_sign,
        }
        response = get(f"http://api.general.zevercloud.cn{url}", headers=headers)
        if response.status_code == 400:
            print(response.headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _apply_unit(value: float, unit: str) -> Union[float, int]:
        """
        Given a unit and a value, convert the value to a standardized unit.

        Values are converted to:
        - W (Watt) for power (i.e. the incoming unit is W, kW, MW)
        - kWh (kiloWatt-hour) for yield (i.e. the incoming unit is Wh, kWh, MWh)

        As the Zevercloud API (sometimes) uses incorrect capitalisation (KWh instead of kWh),
        capitalisation is ignored.
        """
        unit = unit.lower()
        if unit.startswith("w"):
            result = value
        elif unit.startswith("k"):
            result = 1000 * value
        elif unit.startswith("m"):
            result = 1_000_000 * value
        else:
            raise ValueError(f"Unrecognized unit: {unit}")
        if unit.endswith("h"):  # We convert yield to kWh
            return result / 1000
        else:
            return int(round(result))

    @property
    def inverters(self) -> List[str]:
        """Get a list of inverter ids associated to your site."""
        result = self._get(f"/getInverterOverview?key={self.api_key}")
        return [entry["isno"] for entry in result["data"]]
