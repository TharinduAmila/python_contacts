import redis

from utils.config import RedisConfig

day_in_seconds = 60 * 60 * 24
month_in_seconds = day_in_seconds * 31

redis_db = redis.StrictRedis(
    host=RedisConfig.host,
    port=RedisConfig.port,
    password=RedisConfig.password
)


def store_invalidated_token_details(token):
    redis_db.setex("token_" + token, day_in_seconds, "True".encode('utf-8'))
    return


def get_invalidated_token(token):
    out = redis_db.get("token_" + token)
    if out is None:
        return None
    else:
        return out.decode('utf-8')


def store_validated_email(email, valid):
    redis_db.setex("email_" + email, month_in_seconds, valid.encode('utf-8'))
    return


def get_validated_email(email):
    out = redis_db.get("email_" + email)
    if out is None:
        return None
    else:
        return out.decode('utf-8')
