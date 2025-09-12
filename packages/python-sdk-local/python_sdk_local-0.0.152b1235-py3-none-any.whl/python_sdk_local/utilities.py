import inspect  # noqa
import json
import os
import random
import re
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from urllib.parse import urlparse
import jwt
import requests
from dotenv import load_dotenv

from python_sdk_remote.mini_logger import MiniLogger as logger

load_dotenv()
# If DOTENV_PATH is defined, load the environment variables from the specified file
# If OVERRIDE_DOTENV is set to True, override the existing environment variables
override = True if os.getenv("OVERRIDE_DOTENV", "").lower() in (
    "t", "true", "0") else False
load_dotenv(dotenv_path=os.environ.get("DOTENV_PATH"),
            override=override)  # add another .env file if needed

# raise Exception("Failed to load environment variables from .env file\n"
#                 "Please check if the file exists, maybe you are not in the right venv?")

# TODO: add cache with/out timeout decorator

# TODO Use the const/enum from the language package
DEFAULT_LANG_CODE_STR = "en"
# TODO If no one is using DEFAULT_DATETIME_FORMAT, let's comment it
# TODO Let's split DEFAULT_DATETIME_FORMAT into two const 1. Displayable to Humans (MMM) 2. Internal (sortable) with %m
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def append_if_not_exist(lst: list, item: object) -> None:
    if item not in lst:
        lst.append(item)


def to_dict(data: dict | None) -> dict:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    return json.loads(data)


def to_json(data: dict | None) -> json:
    if data is None:
        data = {}
    if isinstance(data, dict):
        json_data = json.dumps(data, default=str)
        return json_data
    return data


def timedelta_to_time_format(time_delta: timedelta) -> str:
    """
    Convert a timedelta to a time format in HH:MM:SS.

    Parameters:
        time_delta (datetime.timedelta): The timedelta to be converted.

    Returns:
        str: A string in HH:MM:SS format representing the time duration.

    Example:
        Usage of timedelta_to_time_format:

        >>> from datetime import timedelta
        >>> duration = timedelta(hours=2, minutes=30, seconds=45)
        >>> formatted_time = timedelta_to_time_format(duration)
        >>> print(formatted_time)
        "02:30:45"
    """
    TIMEDELTA_TO_TIME_FORMAT_METHOD_NAME = "timedelta_to_time_format"
    logger.start(TIMEDELTA_TO_TIME_FORMAT_METHOD_NAME,
                 object={'time_delta': time_delta})

    # Calculate the total seconds and convert to HH:MM:SS format
    total_seconds = int(time_delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format as "HH:MM:SS"
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    logger.end(TIMEDELTA_TO_TIME_FORMAT_METHOD_NAME,
               object={'formatted_time': formatted_time})
    return formatted_time


def is_valid_time_range(time_range: tuple) -> bool:
    """
    Validate that the time range is in the format 'HH:MM:SS'.
    """
    logger.start(object={"time_range": time_range.__str__()})
    if len(time_range) != 2:
        logger.end(object={"is_valid_time_range_result": False,
                   "reason": "len(time_range) != 2"})
        return False

    for time_obj in time_range:
        if not isinstance(time_obj, time):
            logger.end(object={
                "is_valid_time_range_result": False, "reason": "time_range contains non-time objects"})
            return False
        time_str = time_obj.strftime('%H:%M:%S')
        if time_obj.strftime('%H:%M:%S') != time_str:
            logger.end(object={
                "is_valid_time_range_result": False, "reason": "time_range contains invalid time format"})
            return False

    logger.end(object={"is_valid_time_range_result": True})
    return True


# TODO shall we also use Url type and not only str? - Strongly Type which I prefer
#   (if yes we should change it also in all the calls to this function)
def validate_url(url: str):
    logger.start(object={"url": url})
    if url is not None or url != "":
        parsed_url = urlparse(url)
        is_valid_url = parsed_url.scheme and parsed_url.netloc
    else:
        is_valid_url = True
    logger.end(object={"is_valid_url": is_valid_url})
    return is_valid_url


def is_valid_date_range(date_range: tuple) -> bool:
    """
    Validate that the date range is in the format 'YYYY-MM-DD'.
    """
    logger.start(object={"date_range": date_range.__str__()})
    if len(date_range) != 2:
        logger.end(object={"is_valid_date_range_result": False,
                   "reason": "len(date_range) != 2"})
        return False

    for date_obj in date_range:
        if not isinstance(date_obj, date):
            logger.end(object={
                "is_valid_date_range_result": False, "reason": "date_range contains non-date objects"})
            return False
    logger.end(object={"is_valid_date_range_result": True})
    return True


def is_valid_datetime_range(datetime_range: tuple[datetime, datetime]) -> bool:
    """
    Validate that the datetime range is in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    logger.start(object={"datetime_range": datetime_range.__str__()})
    if len(datetime_range) != 2:
        logger.end(object={"is_valid_datetime_range_result": False,
                   "reason": "len(datetime_range) != 2"})
        return False

    if not all(isinstance(datetime_obj, datetime) for datetime_obj in datetime_range):
        logger.end(object={"is_valid_datetime_range_result": False,
                           "reason": "datetime_range contains non-datetime objects"})
        return False
    logger.end(object={"is_valid_datetime_range_result": True})
    return True


def is_list_of_dicts(obj: object) -> bool:
    """
    Check if an object is a list of dictionaries.

    Parameters:
        obj (object): The object to be checked.

    Returns:
        bool: True if the object is a list of dictionaries, False otherwise.

    Example:
        Usage of is_list_of_dicts:

        >>> is_list_of_dicts([{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}])
        True

        >>> is_list_of_dicts([1, 2, 3])
        False

        >>> is_list_of_dicts(1)
        False
    """
    logger.start(object={"obj": obj})
    try:
        if not isinstance(obj, list):
            is_list_of_dicts_result = False
            logger.end(
                object={"is_list_of_dicts_result": is_list_of_dicts_result})
            return is_list_of_dicts_result
        for item in obj:
            if not isinstance(item, dict):
                is_list_of_dicts_result = False
                logger.end(object={
                    "is_list_of_dicts_result": is_list_of_dicts_result})
                return is_list_of_dicts_result
        is_list_of_dicts_result = True
        logger.end(object={
            "is_list_of_dicts_result": is_list_of_dicts_result})
        return is_list_of_dicts_result
    except Exception as exception:
        logger.exception(object=exception)
        logger.end()
        raise


def is_time_in_time_range(check_time: time, time_range: tuple) -> bool:
    """
    Check if the given time is within the specified time range.

    Parameters:
        check_time (str): The time to check in 'HH:MM:SS' format.
        time_range (tuple): A tuple containing start and end times in 'HH:MM:SS' format.

    Returns:
        bool: True if the check_time is within the time range, False otherwise.
    """
    logger.start(object={
        "check_time": check_time.__str__(), "time_range": time_range.__str__()})
    if not is_valid_time_range(time_range) or not isinstance(check_time, time):
        logger.end(object={
            "is_time_in_time_range_result": False})
        return False
    start_time, end_time = time_range
    logger.end(object={
        "is_time_in_time_range_result": start_time <= check_time <= end_time})
    return start_time <= check_time <= end_time


def is_date_in_date_range(check_date: date, date_range: tuple) -> bool:
    """
    Check if the given date is within the specified date range.

    Parameters:
        check_date (str): The date to check in 'YYYY-MM-DD' format.
        date_range (tuple): A tuple containing start and end dates in 'YYYY-MM-DD' format.

    Returns:
        bool: True if the check_date is within the date range, False otherwise.
    """
    logger.start(object={
        "check_date": check_date.__str__(), "date_range": date_range.__str__()})
    if not is_valid_date_range(date_range) or not isinstance(check_date, date):
        logger.end(object={
            "is_date_in_date_range_result": False})
        return False

    start_date, end_date = date_range
    logger.end(object={
        "is_date_in_date_range_result": start_date <= check_date <= end_date})
    return start_date <= check_date <= end_date


def is_datetime_in_datetime_range(check_datetime: datetime, datetime_range: tuple[datetime, datetime]) -> bool:
    """
    Check if the given datetime is within the specified datetime range.

    Parameters:
        check_datetime (str): The datetime to check in 'YYYY-MM-DD HH:MM:SS' format.
        datetime_range (tuple): A tuple containing start and end datetimes in 'YYYY-MM-DD HH:MM:SS' format.

    Returns:
        bool: True if the check_datetime is within the datetime range, False otherwise.
    """
    logger.start()
    if not is_valid_datetime_range(datetime_range) or not isinstance(check_datetime, datetime):
        logger.end(object={
            "is_valid_datetime_range": False})
        return False

    start_datetime, end_datetime = datetime_range
    is_datetime_in_datetime_range_result = start_datetime <= check_datetime <= end_datetime
    logger.end(object={
        "is_datetime_in_datetime_range_result": is_datetime_in_datetime_range_result})
    return is_datetime_in_datetime_range_result


def encode_jwt(payload: dict, key: str) -> str:
    """Example:
    payload = {
        "user_id": 123,
        "username": "john_doe",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    """
    return jwt.encode(payload, key, algorithm='HS256')


def decode_jwt(token: str, key: str) -> dict:
    """key can be private / public"""
    return jwt.decode(token, key, algorithms=['HS256'])


# TODO: add tests to the following functions

def remove_digits(text: str) -> str:
    return ''.join(i for i in text if not i.isdigit())


def generate_otp():
    """Generates a 6-digit OTP"""
    otp = random.randint(100000, 999999)
    return otp


def get_current_datetime_string(datetime_format: str = DEFAULT_DATETIME_FORMAT, tz: timezone = None) -> str:
    current_datetime_string = datetime.now(tz).strftime(datetime_format)
    return current_datetime_string


def datetime_from_str(date_str: str, datetime_format: str = DEFAULT_DATETIME_FORMAT) -> datetime:
    return datetime.strptime(date_str, datetime_format)


def datetime_to_str(input_datetime: datetime, datetime_format: str = DEFAULT_DATETIME_FORMAT) -> str:
    return input_datetime.strftime(datetime_format)


def validate_arguments(args: dict) -> None:
    """
    Validate method arguments to ensure they are not None or ''
    :param args: arguments to be validated (usually locals())
    :return: True if all arguments are not None or '', False otherwise
    """
    for arg, value in args.items():
        if not arg:
            raise ValueError(
                f"Argument {arg} is cannot be empty (got {value})")


def reformat_time_string(input_str: str) -> str:
    """Example:
    "1234" -> "12:34:00:00"
    """
    hours = input_str[:2]
    minutes = "00" if len(input_str) < 4 else input_str[2:4]
    seconds = "00" if len(input_str) < 6 else input_str[4:6]
    milliseconds = "00" if len(input_str) < 8 else input_str[6:8]
    # TODO Shall we use DEFAULT_DATETIME_FORMAT and have the formats in the central
    time_format = f"{hours}:{minutes}:{seconds}:{milliseconds}"
    return time_format


@lru_cache(maxsize=1)
def get_ip_v4():
    # Switched from ipv4.seeip.org to api.ipify.org to avoid SSL handshake issues with OpenSSL 3 in subprocess/multiprocessing environments.
    # return requests.get('https://ipv4.seeip.org/jsonip').json()['ip']
    default_ipv4 = "127.0.0.1"
    try:
        response = requests.get('https://api.ipify.org?format=json').json()
        ipv4_address = response.get('ip', default_ipv4)
        return ipv4_address
    except requests.exceptions.SSLError:
        logger.error("SSL Error while fetching IPv4 address. "
                     f"Defaulting to{default_ipv4}")
        return default_ipv4


@lru_cache(maxsize=1)
def get_ip_v6():
    # return requests.get('https://api.seeip.org/jsonip').json()['ip']
    default_ipv6 = "::1"
    try:
        response = requests.get('https://api64.ipify.org?format=json').json()
        ipv6_address = response.get('ip', default_ipv6)
        return ipv6_address
    except requests.exceptions.SSLError:
        logger.error("SSL Error while fetching IPv6 address. "
                     f"Defaulting to {default_ipv6}")
        return default_ipv6


def snake_to_camel(snake_str: str) -> str:
    """Converts snake_case to camelCase."""
    components = snake_str.split('_')
    camel_str = components[0] + ''.join(x.title() for x in components[1:])
    return camel_str


def camel_to_snake(camel_str: str) -> str:
    """Converts camelCase to snake_case."""
    snake_str = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    return snake_str


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if val is None:
        return 0
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))
