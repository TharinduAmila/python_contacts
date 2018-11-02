import neverbounce_sdk

from utils import config

client = neverbounce_sdk.client(api_key=config.ApiKeys.neverbounce)


# TODO add redis cache for emails
def single_email_check(email):
    verification = client.single_check(email=email, address_info=True)
    # unless result is invalid or disposable we will allow contact creation
    return verification['result'] != "invalid" and verification['result'] != "disposable"
