from datetime import date, datetime
from typing import Dict, Any

from pytest import approx, fixture, mark

from zevercloud import ZeverCloud
from zevercloud.event import ZeverSolarEvent


class MockedZeverCloud(ZeverCloud):
    def __init__(self, result):
        super().__init__("x", "y", "z")
        self.urls = []
        self.result = result

    def _get(self, url: str) -> Dict[str, Any]:
        self.urls.append(url)
        return self.result


class TestProperties:
    @fixture()
    def mocked_cloud(self) -> MockedZeverCloud:
        return MockedZeverCloud(
            result={
                "sid": 12345,
                "ludt": "2022-02-03 13:57:26",
                "status": "0",
                "E-Today": {"unit": "KWh", "value": 5.9},
                "E-Month": {"unit": "KWh", "value": 218.42},
                "E-Total": {"unit": "MWh", "value": 5.8},
                "TotalYield": {"unit": "€", "value": 1218.56},
                "CO2Avoided": {"unit": "T", "value": 5.8},
                "Power": {"unit": "W", "value": 0},
                "E-Year": {"unit": "MWh", "value": 1.77},
            }
        )

    def test_overview(self, mocked_cloud):
        assert mocked_cloud.overview == {
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


class TestGetOutput:
    def test_output(self):
        cloud = MockedZeverCloud(
            {
                "sid": 893,
                "dataunit": "KW",
                "data": [
                    {"time": "00:00", "no": "0", "value": "0.0"},
                    {"time": "00:20", "no": "2", "value": "1.1"},
                    {"time": "00:40", "no": "4", "value": "2.2"},
                ],
            }
        )
        assert cloud.get_output(date=date(2022, 1, 1)) == [
            {"power": 0, "timestamp": datetime(2022, 1, 1, 0, 0)},
            {"power": 1100, "timestamp": datetime(2022, 1, 1, 0, 20)},
            {"power": 2200, "timestamp": datetime(2022, 1, 1, 0, 40)},
        ]
        assert cloud.urls == ["/getPlantOutput?date=2022-01-01&key=x&period=bydays"]

    def test_daily_output(self):
        cloud = MockedZeverCloud(
            {
                "dataunit": "KWh",
                "sid": "36",
                "data": [
                    {"time": "2014-04-01", "no": "1", "value": "4.1"},
                    {"time": "2014-04-02", "no": "2", "value": "5.2"},
                    {"time": "2014-04-03", "no": "3", "value": "0.2"},
                ],
            }
        )
        assert cloud.get_daily_output(month=date(2014, 4, 15)) == [
            {"date": date(2014, 4, 1), "yield": 4.1},
            {"date": date(2014, 4, 2), "yield": 5.2},
            {"date": date(2014, 4, 3), "yield": 0.2},
        ]
        assert cloud.urls == ["/getPlantOutput?date=2014-04&key=x&period=bymonth"]

    def test_monthly_output(self):
        cloud = MockedZeverCloud(
            {
                "dataunit": "KWh",
                "sid": "36",
                "data": [
                    {"time": "2014-01", "no": "1", "value": "40.1"},
                    {"time": "2014-02", "no": "2", "value": "52.1"},
                    {"time": "2014-03", "no": "3", "value": "113"},
                    {"time": "2014-04", "no": "4", "value": "8.11"},
                ],
            }
        )
        assert cloud.get_monthly_output(year=2014) == [
            {"date": date(2014, 1, 1), "yield": 40.1},
            {"date": date(2014, 2, 1), "yield": 52.1},
            {"date": date(2014, 3, 1), "yield": 113},
            {"date": date(2014, 4, 1), "yield": 8.11},
        ]
        assert cloud.urls == ["/getPlantOutput?date=2014&key=x&period=byyear"]

    def test_yearly_output(self):
        cloud = MockedZeverCloud(
            {
                "dataunit": "MWh",
                "sid": "36",
                "data": [{"time": "2012", "no": "1", "value": "4.069"}, {"time": "2013", "no": "2", "value": "0.308"}],
            }
        )
        assert cloud.get_yearly_output() == [
            {"year": 2012, "yield": 4069},
            {"year": 2013, "yield": 308},
        ]
        assert cloud.urls == ["/getPlantOutput?key=x&period=bytotal"]


class TestGetEvents:
    def test_url(self):
        cloud = MockedZeverCloud(dict(code=0))
        events = cloud.get_events(date(2022, 1, 1), date(2022, 1, 3))
        assert events == []
        assert cloud.urls == ["/getPlantEvent?edt=2022-01-03&key=x&sdt=2022-01-01"]

    def test_result(self):
        cloud = MockedZeverCloud(
            dict(data=[dict(eventType=101, eventCode=3, ssno="ZS12345678", eventTime="2022-01-01 12:34:56")])
        )
        events = cloud.get_events(date(2022, 1, 1), date(2022, 1, 3))
        assert events == [
            ZeverSolarEvent(
                event_time=datetime(2022, 1, 1, 12, 34, 56), inverter_id="ZS12345678", event_code=3, event_type=101
            )
        ]

    def test_multiple_urls(self):
        cloud = MockedZeverCloud(dict(code=0))
        cloud.get_events(date(2022, 1, 1), date(2022, 2, 3))
        assert cloud.urls == [
            "/getPlantEvent?edt=2022-01-07&key=x&sdt=2022-01-01",
            "/getPlantEvent?edt=2022-01-14&key=x&sdt=2022-01-08",
            "/getPlantEvent?edt=2022-01-21&key=x&sdt=2022-01-15",
            "/getPlantEvent?edt=2022-01-28&key=x&sdt=2022-01-22",
            "/getPlantEvent?edt=2022-02-03&key=x&sdt=2022-01-29",
        ]


class TestApplyUnit:
    @mark.parametrize(
        "value, unit, expected", [(5.9, "KW", 5900), (1.2, "MW", 1_200_000), (4.01, "kW", 4010), (8, "W", 8)]
    )
    def test_power(self, value, unit, expected):
        result = ZeverCloud._apply_unit(value, unit)
        assert result == approx(expected)
        assert isinstance(result, int)

    @mark.parametrize("value, unit, expected", [(5.9, "KWh", 5.9), (1.2, "MWh", 1200), (800, "Wh", 0.8)])
    def test_yield(self, value, unit, expected):
        result = ZeverCloud._apply_unit(value, unit)
        assert result == approx(expected)
        assert isinstance(result, float)
