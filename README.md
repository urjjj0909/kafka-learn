# Kafka-learn
參考[海邊的 Kafka 與 Python - Part 1](https://myapollo.com.tw/zh-tw/python-kafka-part-1/)一文，Apache Kafka是知名的分散式串流資料平台（Distributed streaming platform），一開始是由LinkedIn所開發用來收集提交日誌的訊息佇列系統（Messaging queue system），讓應用程式可以訂閱（Subscribe）與發佈（Publish）資料，例如App 可以透過伺服器所提供的API發佈使用者所在位置到Kafka ，而所有訂閱的子系統或應用程式都能夠同時接收到這些資料並即時進行分析與處理。

## 以Docker建立Kafka環境
首先，至`wurstmeister/kafka-docker`將專案複製到本地：

```
mkdir kafka
cd kafka
git clone https://github.com/wurstmeister/kafka-docker
cd kafka-docker
```

並將其中的`docker-compose.yml`進行部分修改：

```
version: '2'
services:
  zookeeper:
    image: wurstmeister/zookeeper
    ports:
      - "2181:2181"
    restart: unless-stopped

  kafka:
    image: wurstmeister/kafka
    depends_on: [ zookeeper ]
    ports:
      - "9092:9092"
    expose:
      - "9093"
    environment:
      KAFKA_ADVERTISED_LISTENERS: INSIDE://kafka:9093,OUTSIDE://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT
      KAFKA_LISTENERS: INSIDE://0.0.0.0:9093,OUTSIDE://0.0.0.0:9092
      KAFKA_INTER_BROKER_LISTENER_NAME: INSIDE
      KAFKA_CREATE_TOPICS: "test:1:1"
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

在以上程式碼中，利用`docker-compose.yml`建立多個容器（Container），每個容器都會跑起來一個自己的服務，而構成一個服務的最基礎設定單元有以下幾個：
* `image`：代表這個容器要跑什麼服務，基本上會到Docker hub下載（Pull）映像檔，也可以自己做一個映像檔出來
* `ports`：容器端點（Endpoint）和外部端點間的關係
* `environment`：這個服務的要設定的環境變數
* `volumes`：容器內部資料和外部資料間的掛載關係

其中，在`ports`設定中，前者代表`HOST_PORT`而後者代表`CONTAINER_PORT`，假設我們目前使用Windows主機，那麼外部的Host就是我們的Windows環境。二者的區別在於，容器網路中的服務間使用的是 `CONTAINER_PORT`通訊，而`HOST_PORT`定義了是為了容器網路外被呼叫的，舉例說明如下：

```
...
  db:
    image: postgres
    ports:
      - "8001:5432" // HOST_PORT:CONTAINER_PORT
...
```

假設有一個postgres服務的端點設定關係如上，假設外部需要和資料庫做連線需使用`postgres://db:8081`、若容器間的服務需要和資料庫做連線則使用`postgres://db:5432`。外部並不會察覺`8081 Port`的存在，而這個Port通常是資料庫安裝時的預設端點；此外，`expose`代表跑在容器內的服務可以互相溝通的Port，外部是無法透過此Port和內部溝通，其實就是`CONTAINER_PORT`的概念。

不論是透過內部、外部取用容器服務，網路端點是在Docker中很重要的概念，列下幾篇講解詳細的參考文獻：

* [What is the difference between docker-compose ports vs expose](https://stackoverflow.com/questions/40801772/what-is-the-difference-between-docker-compose-ports-vs-expose)
* [Day 26-三周目-Docker基本使用：看完就會架docker化的服務](https://ithelp.ithome.com.tw/articles/10205481)
* [Docker Compose方式下的容器網路基礎知識點](https://www.gushiciku.cn/pl/2XVH/zh-tw)
* [Day 29-三周目-Docker Compose：一次管理多個容器](https://ithelp.ithome.com.tw/articles/10206437)

## Docker+Kafka指令
首先，我們先把Docker容器跑起來，再用`docker ps`確認是否啟動成功：

```
docker-compose -f docker-compose.yml up -d
docker ps
```

假設要讓容器「停止（stop）」或「停止並刪除（Down）」則分別使用：

```
docker-compose -f docker-compose.yml stop
docker-compose -f docker-compose.yml down
```

我們可以直接到跑起來的容器當中去使用指令集做操作：

```
docker exec -it kafka-docker-kafka-1 bash
cd $KAFKA_HOME/bin
pwd
```

以下分別做「建立一個`my-test-topic`的主題（Topic）」、「列出所有主題」和「列出某主題詳細資料」：

```
kafka-topics.sh --create --zookeeper zookeeper:2181 --replication-factor 1 --partitions 1 --topic my-test-topic
kafka-topics.sh --list --zookeeper zookeeper:2181
kafka-topics.sh --zookeeper zookeeper:2181 --topic my-test-topic --describe
```

最後，我們可在容器內測試生產者（Producer）和消費者（Consumer）是否成功運作：

```
kafka-console-producer.sh --topic=my-test-topic --broker-list localhost:9092
kafka-console-consumer.sh --bootstrap-server localhost:9092 --from-beginning --topic my-test-topic
```

以上指令操作可以交互參考[Docker部署单节点Kafka](https://www.cnblogs.com/kendoziyu/p/15129948.html)進行。

## Python+Kafka外部操作
這裡稱作外部操作是由於我們在本機端以Python程式（在容器外的即視為外部Host）和容器內部的Kafka Server溝通。

以下為`producer.py`：

```
from kafka import KafkaProducer
from kafka.errors import KafkaError

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    linger_ms=1000,
    batch_size=1000,
    api_version=(2,0,2)
)

# Asynchronous by default.
future = producer.send('my-test-topic', b'raw_bytes')
print(future)

msg = "hello! kafka!"

# Produce asynchronously.
for _ in range(1000):
    producer.send('my-test-topic', msg.encode('utf-8'))

# Block until all async messages are sent.
producer.flush()

# Block for "synchronous" sends.
try:
    record_metadata = future.get(timeout=10)
    print(record_metadata)
except KafkaError:
    pass # decide what to do if produce request failed...

# Successful result returns assigned partition and offset.
print(record_metadata.topic)
print(record_metadata.partition)
print(record_metadata.offset)
```

以下為`consumer.py`：

```
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'my-test-topic',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='latest',
    api_version=(2,0,2)
)

for message in consumer:
    print(message)
    print('%s:%d:%d: key=%s value=%s' % \
        (message.topic, message.partition, message.offset, message.key, message.value)
    )
```

以上程式碼輸出結果可以參考[海邊的 Kafka 與 Python - Part 2](https://myapollo.com.tw/zh-tw/python-kafka-part-2/)一文，到此我們完成了以下工作：

1. 利用`docker-compose.yml`建立一個Kafka服務
2. 設定內外部端點關係、資料掛載關係
3. 利用Python腳本`producer.py`寫資料到容器內Kafka topic
4. 利用Python腳本`consumer.py`把容器內Kafka topic的資料讀出來

## Kafka-MongoDB Microservice
假設今天要實作一個接收資料（Source）後存放到資料庫（Sink）的架構，我們可以在一個容器中把Kafka和MongoDB跑起來，並利用外部程式做邏輯和計算上的操作，整體資訊架構和操作步驟如下：

1. 以request去訪問網頁的資訊作為`Data souce`
2. 實作`https-kafka-microservice`：將爬取的資訊以Kafka producer寫入`my-test-topic`中
3. 實作`kafka-mongo-microservice`：利用Kafka consumer訂閱`my-test-topic`，並讀取其中資訊存放至MongoDB中

<div align=center><img src="https://user-images.githubusercontent.com/100120881/172556695-4a668d53-1fef-485b-b5e0-7dcd2fa54bc2.png" width="800"></div>

首先，為了將MongoDB服務跑起來，我們在`docker-compose.yml`加入`mongodb`相關設定：

```
...
  mongodb:
    image: mongo
    ports:
      - "27018:27017" // 注意對外的port=27018
    volumes:
      - {PATH_FOR_LOCAL_DIR}:/data/db // SOURCE:TARGET
...
```

在`volumes`中的的格式是`SOURCE:TARGET`，其中的`SOURCE`可以來自Host或是Volume，前者表示將本機端的資料夾或檔案掛載至`TAEGET`、後者表示將容器內其餘服務的Volume實體掛載至`TAEGET`，且不管`SOURCE`來自哪裡，都不會因為容器刪除後而導致檔案遺失。在此例中，我將本機的資料夾路徑`PATH_FOR_LOCAL_DIR`掛載到`mongodb`這個服務中的`/data/db`中。

跑起來後在Docker Desktop應該可以看到以下畫面（服務名稱可能略有不同）：

<div align=center><img src="https://user-images.githubusercontent.com/100120881/172561781-4d1bfa65-e5c3-4eb4-91d6-c1cfc9bbe849.png"></div>

其中，紅色框線處代表我們可以直接使用這個服務的bash terminal。假設要用`mongodb`服務，可以直接在這個bash terminal中使用它的指令集對資料庫做操作：[Shell Quick Reference](https://www.mongodb.com/docs/manual/reference/mongo-shell/#mongo-shell-quick-reference)，這和從本機的terminal直接使用`docker exec -it kafka-docker-mongodb-1 bash`是一模一樣的。

最後，`https-kafka-microservice`程式碼`https-kafka.py`如下：

```
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
```

`kafka-mongo-microservice`程式碼`kafka-mongo.py`如下：

```
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
```

最後，如果成功跑起來，應該就可以用MongoDB Compass連線到`mongodb://localhost:27018`看到有資料成功寫入：

<div align=center><img src="https://user-images.githubusercontent.com/100120881/172565088-c550fbfe-03a4-49a7-b20c-4f1a62c9856e.png"></div>

## 注意事項
* 參考Stackoverflow[本篇](https://stackoverflow.com/questions/58938753/how-to-create-a-database-in-mongo-using-python)得知在創建MongoDB的db/collection時，直到你實際寫入document前它們都不會建立（Lazily created）
