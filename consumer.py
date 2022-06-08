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
