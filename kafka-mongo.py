from kafka import KafkaConsumer
import pymongo
import json

# 外部訪問容器裡的MongoDB，注意Port是27018
client = pymongo.MongoClient("mongodb://localhost:27018/")

# 初始化一個名為「database」資料庫，並在這個資料庫中建立一個名為「test」的collection
db = client["database"]
collection = db["test"]

# KafkaConsumer()並設定僅讀取最新資料
consumer = KafkaConsumer(
    'my-test-topic',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='latest',
    api_version=(2,0,2)
)

# 把從Topic中讀取的資料印出來並寫入MongoDB中
for message in consumer:
    print(message)
    print('%s:%d:%d: key=%s value=%s' % (message.topic, message.partition, message.offset, message.key, message.value))
    x = collection.insert_one(json.loads(message.value))
    print(x.inserted_id)