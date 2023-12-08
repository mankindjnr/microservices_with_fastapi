from main import redis, ProductRedis
import time

key = 'order_completed'
group = 'inventory-group'

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
                try:
                    product = ProductRedis.get(obj['product_id'])
                    # check if the product exists - if it exists update stock, else send event back to initialize refund
                    product.quantity -= int(obj['quantity'])
                    product.save()
                except:
                    redis.xadd('refund_order', obj, '*')
    except Exception as e:
        print(str(e))
    time.sleep(1)