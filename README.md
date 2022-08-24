# Zevercloud API

Python API for the Zevercloud API

**Note**: _This piece of software is not approved or endorsed by ZeverCloud. Nor do I endorse their products._

## Installation

You can install `zevercloud-api` using your favorite package manager. For example:

```shell
pip install zevercloud-api
```

## Credentials

Three keys are needed to connect to the Zevercloud API:
- `api_key`
- `app_key`
- `app_secret`

Your `api_key` can be found on the Zevercloud site, under `Configuration > Plant Configuration > 5. Api Key`.
The `app_key` and `app_secret` can be found under `Account Management > Security Settings`, but are only 
visible once approved by Zeversolar Support. Send an email to service.eu@zeversolar.net, for example, and
ask them to make the `app_key` and `app_secret` visible to you. They typically do so within a day.

## Usage

To see the last known status of your site, as well as some yield statistics:
```python
from zevercloud import ZeverCloud

zc = ZeverCloud(API_KEY, APP_KEY, APP_SECRET)

print(zc.overview)
```
```shell
>>  {
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
```

### Historical power and yield

Historical yield and power figures can also be obtained:
```python
zc.get_output(date=date(2022, 8, 1))
```
```shell
>>  [
       ...
        {"power": 1183, "timestamp": datetime(2022, 8, 1, 12, 0)},
        {"power": 1240, "timestamp": datetime(2022, 8, 1, 12, 20)},
        {"power": 1815, "timestamp": datetime(2022, 8, 1, 12, 40)},
        ...
    ]
```

```python
zc.get_daily_output(month=date(2022, 8, 1))
```
```shell
>>  [
        {"date": date(2022, 3, 1), "yield": 4.1},
        {"date": date(2022, 8, 2), "yield": 5.2},
        {"date": date(2022, 8, 3), "yield": 0.2},
        ...
    ]
```

```python
zc.get_monthly_output(year=2022)
```
```shell
>>  [
       {"date": date(2022, 1, 1), "yield": 40.1},
       {"date": date(2022, 2, 1), "yield": 52.1},
       {"date": date(2022, 3, 1), "yield": 113},
       {"date": date(2022, 4, 1), "yield": 8.11},
        ...
    ]
```

```python
zc.get_yearly_output()
```
```shell
>>  [
       {"year": 2012, "yield": 4069},
       {"year": 2013, "yield": 308},
        ...
    ]
```


Power is always presented in W (Watt), and yield in kWh (kiloWatt-hour). Due to the
internals of the Zevercloud API, all numbers may be rounded up to two significant digits.

### Events

Events (errors) can be listed:
```python
zc.get_events(start_date=date(2022, 1, 1), end_date=date(2022, 8, 1))
```
```shell
>>  [
        ZeverSolarEvent(
            event_time=datetime(2022, 1, 1, 12, 34, 56), 
            inverter_id="ZS12345678", 
            event_code=3, 
            event_type=101,
        )
    ]
```

The `ZeverSolarEvent` has a human-readable `event_description`.

**Note**: the internal Zevercloud API can only return events for 7 days at a time. Using
the `get_events`-method on a large date range will result in many API-calls being made,
and may hence possibly take a rather long time.
