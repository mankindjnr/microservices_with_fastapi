from redis_om import get_redis_connection, HashModel

redis = get_redis_connection(
    host="redis-12603.c326.us-east-1-3.ec2.cloud.redislabs.com",
    port=12603,
    password="prnrNkgQiIEFP5a0mBV63luOw6CRvyfB",
    decode_responses=True
)

try:
    # Ping the Redis server
    if redis.ping():
        print("Redis connection is working fine.")
    else:
        print("There seems to be a problem with the Redis connection.")
except Exception as e:
    print(f"An error occurred: {e}")

