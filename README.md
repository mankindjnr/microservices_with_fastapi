# MICROSERVICES WITH FASTAPI AND REDIS

For this project, i will have two microservices, i'll have the inventory microservice and the order microservice. The inventory microservice will be responsible for keeping track of the inventory of the products in the store. The order microservice will be responsible for keeping track of the orders placed by the customers. Both microservices will be using Redis as the database.

inventory == inventory microservice
order == payments microservice

### installations
```bash
pip install fastapi[all]
pip install redis-om
```

### connecting to a redis server
```python
from fastapi import FastAPI
from redis_om import get_redis_connection


app = FastAPI()

mankindjnrdb = get_redis_connection(
    host="redis-12603.c326.us-east-1-3.ec2.cloud.redislabs.com",
    port=12603,
    password="prnrNkgQiIEFP5a0mBV63luOw6CRvyfB",
    decode_responses=True
)
```

### creating models that will turn to tables in the database
```python
class Product(HashModel):
    name: str
    price: float
    quantity: int

    class Meta:
        database = mankindjnrdb

```
This is the equivalent of a django model. The class name will be the name of the table in the database. The class attributes will be the columns in the table.

`In the given Python code, a class Product is defined which inherits from HashModel. This class represents a model similar to Django but for a NoSQL database like Redis. It has three fields: name, price, and quantity. The Meta class is defining metadata for the Product class - in this case, specifying that the database for this model is mankindjnrdb(db name).`

### creating a route to add a product to the database
For this section, i have two models, one for the pydantic model so as fastApi can validate the data and the other for the redis model so as to save the data in the database.


```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "https://sj76vr3h-8000.euw.devtunnels.ms", ],
    #allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductModel(BaseModel):
    name: str
    price: float
    quantity: int

    class Config:
        orm_mode = True

class ProductRedis(HashModel):
    name: str
    price: float
    quantity: int

    class Meta:
        database = redis

@app.post('/products')
def create(product: Product):
    return product.save()

```

### A route to query all products fromt the redis database
This returns all the primary keys of the products in the database

```python

@app.get("/products")
def all():
    return Product.all_pks()
```

We proceed to create the delete method and get product by id.
The crud part is complete. We can now proceed to the order microservice. (payments)

***
***
***
# PAYMENTS MICROSERVICE

the idea of microservice is that every microservice needs a different database. So for this microservice, i will be using a different database.

__you can connect or use a postgres/mongodb or even redis database for this microservice__

```python
from fastapi import FastAPI, status, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis_om import get_redis_connection, HashModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import requests

from models import OrderModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "https://sj76vr3h-8000.euw.devtunnels.ms", ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This should be a different database than the one used by the inventory service
redis = get_redis_connection(
    host="redis-12603.c326.us-east-1-3.ec2.cloud.redislabs.com",
    port=12603,
    password="prnrNkgQiIEFP5a0mBV63luOw6CRvyfB",
    decode_responses=True
)

class OrderRedis(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str # pending, paid, cancelled, refunded

    class Meta:
        database = redis


@app.post("/orders")
async def create(request: Request):
    body = await request.json()

    req = requests.get(f"http://127.0.0.1:8000/products/{body['product_id']}") #we are getting a response from the other microservice
    product = req.json()

    # creating the order
    order = OrderRedis(
        product_id=product['pk'],
        price=product['price'],
        fee = 0.2 * product['price'],
        total = 1.2 * product['price'],
        quantity=body['quantity'],
        status='pending' # we are waiting for the payment processor to complete the payment
    )

    order.save()

    order_completed(order)

    return order

def order_completed(order: OrderRedis):
    order.status = 'paid'
    order.save()
```

the route above creates an order and returns the product details of the product that was ordered. We call the route with a post request `@app.post("/orders")` and we get the product id from the request body `body = await request.json()` and we use the product id to query the product details from the inventory microservice `req = requests.get(f"http://localhost:8000/products/{body['product_id']}")` and we return the product details `return req.json()`

We use `asynchronous` because we are making a request to another microservice and we don't want to block the event loop. With asynchronous, the event loop can continue to run while we wait for the response from the other microservice.

What this means is that we can make multiple requests to the inventory microservice and the event loop will continue to run while we wait for the response from the inventory microservice.

We have also added a simple confirmation that checks if the order has been paid for. This is done by calling the `order_completed` function which changes the status of the order from pending to paid. (later we will improve it)

For the requests to be successful, both microservices should be online, for this the inventory microservice was run using the command 
```bash
uvicorn main:app --reload
```

this will run on port 8000 since fastapi uses it as the default port.

The payments/order microservice will be run using the command
```bash
uvicorn main:app --reload --port 9400
```

this will run on port 9400 since the inventory microservice is already running on port 8000.

### Postman
our order request comes from the second microservice, so we will use postman to make the request. the request looks like this

url = `http://127.0.0.1:9400/orders`
method = `POST`
body = 
```json
{
    "product_id": "1dfhhjttfgf479yhfDSFGJIU",
    "quantity": 2
}
```

The response will include the product details and the order primary key. The order primary key will be used to query the order details.


### Payments Confirmation
In our earlier confirmation function, we did not account for how long merchants take, we will now assume that every transaction takes 5 seconds to complete. We will use the `asyncio.sleep` function to simulate the 5 seconds.

we could have used the `time.sleep` function but it is blocking and will block the event loop. `asyncio.sleep` is non-blocking and will not block the event loop.

Also, when we send the first confirmation message, we want it to state the order status as pending, and when we send the second confirmation message, we want it to state the order status as paid.

```python
def order_completed(order: OrderRedis):
    asyncio.sleep(5)
    order.status = 'paid'
    order.save()
```

### Background Tasks
We will use fastApi's background task to confirm if the order has been paid for.

```python
@app.post("/orders")
async def create(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    req = requests.get(f"http://127.0.0.1:8000/products/{body['product_id']}") #we are getting a response from the other microservice
    product = req.json()

    # creating the order
    ........

    order.save()

    background_tasks.add_task(order_completed, order)

    return order

async def order_completed(order: OrderRedis):
    await asyncio.sleep(40)
    order.status = 'paid'
    order.save()
```

` background_tasks.add_task(order_completed, order)` WHen we call the background task, we pass in the function and the arguments that the function takes. In this case, the function takes the order as an argument.

To test the background task,
```python
@app.get("/orders/{pk}")
def get(pk: str):
    return OrderRedis.get(pk)
```

### Updating the stock

Currently, when an order is completed, the stock/quantity is not updated. 
We will tackle this issue, using `redisstreams`.

__Redisstreams is a messaging event bus that allows us to send messages from one microservice to another. just like Rabbitmq or kafka, We will use it to communicate the two microservices by sending events and they wont know about each other.__

As soon as the order is completed and the status is confirmed/paid,  we will send an event to the inventory microservice to update the stock.

```python
async def order_completed(order: OrderRedis):
    await asyncio.sleep(40)
    order.status = 'paid'
    order.save()

    redis.xadd('order completed', order.dict(), '*')
```

`redis.xadd('order completed', order.dict(), '*')` this line of code sends an event to the inventory microservice. The first argument is the name of the event, the second argument is the data that we want to send and the third argument is the id of the event. The id of the event is set to `*` which means that the id of the event will be auto generated. you can choose to set the id of the event to anything you want.

### Listening for events
in our inventory microservice, we will create the consumer that will wait fo the event.

`inventory/consumer.py`

```python
from main import redis, Product

key = 'order_completed'
group = 'inventory-group'

try:
    redis.xgroup_create(key, group)
except:
    print("group already exists")

while True:
    try:
        results = redis.xreadgroup(group, key, {key: '>'}, None)
    except Exception as e:
        print(str(e))
    time.sleep(1)
```

`this function/try and except block will keep running until it receives an event, it will receive an event when we send an event from the order microservice.`

we are going to run it and then place an order, `python consumer.py`

When consumer.py receives the event, we will use that to update the stock.

```python
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
            for result in results:
                obj = result[1][0][1]
                product = ProductRedis.get(obj['product_id'])
                print(product)
                product.quantity -= int(obj['quantity'])
                product.save()
    except Exception as e:
        print(str(e))
    time.sleep(1)
```

With this, the quantity is decreased as needed without even the microservices knowing what happened to the other microservice.


The xreadgroup function is a part of Redis Streams and is used to read data from a stream using a consumer group.

Here's a breakdown of the parameters:

group: This is the name of the consumer group that is reading the data. Consumer groups are a way to divide the messages in a stream between multiple consumers.
key: This is the name of the stream from which to read the data.
{key: '>'}: This is a special ID that tells Redis to deliver only the messages that were never delivered to any other consumer. If there are no such messages, the command will block until there are.
So, in this case, the xreadgroup function is being used to read new messages from the stream specified by key that have not been delivered to any other consumer in the group.

# Event Driven Architecture basics

### Edge cases
At times a user might place and order and then before the order is completed, the order is deleted from the database but we end up charging the user for a non-existent product, to comabat this, we will add a check to see if the product exists before we charge the user, if so, we refund the user.

For this, we will send from the inventory microservice to the order/payment microservice. We will send from the event that updates the stock.
```python
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
            for result in results:
                obj = result[1][0][1]
                product = ProductRedis.get(obj['product_id'])
                
                # check if the product exists - if it exists update stock, else send event back to initialize refund
                if product:
                    print(product)
                    product.quantity -= int(obj['quantity'])
                    product.save()
                else:
                    redis.xadd('refund_order', obj, '*')
    except Exception as e:
        print(str(e))
    time.sleep(1)
```

This means that we will now have a consumer in the order/payments microservice as well.

```python
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
```
Now when i check the status of the order, it will be refunded.


# FrontEnd

