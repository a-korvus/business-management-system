"""Custom formatters for fields of admin models."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def format_datetime_local(model: type, field_name: Any) -> str:
    """Format datetime field to string value.

    Datetime field value must contain the timezone.

    Args:
        model (type): SQLAlchemy model object.
        field_name (Any):: Datetime field value

    Returns:
        Any: Formatted datetime value.
    """
    field_value = getattr(model, field_name, None)
    if field_value is None:
        return ""

    local_value: datetime = field_value.astimezone(ZoneInfo("Europe/Moscow"))
    return local_value.strftime("%d.%m.%Y %H:%M (%Z)")
