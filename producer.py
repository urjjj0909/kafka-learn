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