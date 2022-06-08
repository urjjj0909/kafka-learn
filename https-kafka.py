from kafka import KafkaProducer
from kafka.errors import KafkaError
import requests
import json
import time

# 訪問一個範例網頁並將其中資料以JSON格式載入
response = requests.get("https://jsonplaceholder.typicode.com/users", verify=False)
results = json.loads(response.text)

# 初始化KafkaProducer()並設定將輸出資料做value_serializer設定
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda m: json.dumps(m).encode(),
    api_version=(2,0,2)
)

# 將資料寫到my-test-topic中
for message in results:
    producer.send('my-test-topic', message)
    time.sleep(.1)

producer.flush()