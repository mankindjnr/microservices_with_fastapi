from main import redis, OrderRedis
import time

key = 'refund_order'
group = 'payment-group'

try:
    redis.xgroup_create(key, group)
except:
    print("group already exists")

while True:
    try:
        results = redis.xreadgroup(group, key, {key: '>'}, None)
        if results != []:
            print(results)
            for result in results:
                obj = result[1][0][1]
                order = OrderRedis.get(obj['pk'])
                
                # change the status of the order
                order.status = "refunded"
                order.save()
    except Exception as e:
        print(str(e))
    time.sleep(1)