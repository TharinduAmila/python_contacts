import re
from typing import Pattern

import phonenumbers as ph

from utils import neverbounce_connector, redis_connector

emailValidationRegex: Pattern[str] = re.compile('^(([^<>()\\[\\]\\\\.,;:\\s@"]+(\\.[^<>()\\[\\]\\\\.,;:\\s@"]+)*)|' +
                                                '(".+"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}])|' +
                                                '(([a-zA-Z\\-0-9]+\\.)+[a-zA-Z]{2,}))$')


def validate_email_format(email):
    if emailValidationRegex.match(email):
        value = redis_connector.get_validated_email(email)
        if value is None:
            value = neverbounce_connector.single_email_check(email)
            redis_connector.store_validated_email(email, str(value))
        else:
            value = (value == "True")
        return value
    else:
        return False


def validate_telephone_number(number):
    try:
        phone_number = ph.parse(number, None)  # expects e164 format
        return ph.is_valid_number(phone_number)
    except ph.NumberParseException:
        return False


def validate_user_contact_details(user):
    return validate_email_format(user.email) and validate_telephone_number(user.telephone)
