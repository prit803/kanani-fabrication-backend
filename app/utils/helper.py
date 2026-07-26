from datetime import date, datetime
from decimal import Decimal


def model_to_dict(model):
    """
    Convert SQLAlchemy model to dictionary.
    Removes SQLAlchemy internal attributes.
    Converts datetime/date/Decimal to JSON serializable values.
    """

    if model is None:
        return None

    data = {}

    for column in model.__table__.columns:

        value = getattr(model, column.name)

        if isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")

        elif isinstance(value, date):
            value = value.strftime("%Y-%m-%d")

        elif isinstance(value, Decimal):
            value = float(value)

        data[column.name] = value

    return data


def models_to_list(models):
    """
    Convert SQLAlchemy model list to list of dictionaries.
    """

    return [model_to_dict(model) for model in models]


def get_current_datetime():
    """
    Return current datetime.
    """

    return datetime.now()


def is_null_or_empty(value):
    """
    Check whether value is None or empty string.
    """

    if value is None:
        return True

    if isinstance(value, str) and value.strip() == "":
        return True

    return False


def safe_strip(value):
    """
    Remove spaces from string safely.
    """

    if value is None:
        return None

    return value.strip()


def safe_upper(value):
    """
    Convert string to uppercase safely.
    """

    if value is None:
        return None

    return value.upper()


def safe_lower(value):
    """
    Convert string to lowercase safely.
    """

    if value is None:
        return None

    return value.lower()