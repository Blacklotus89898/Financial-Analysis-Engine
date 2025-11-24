import time
import json
import yfinance as yf
from kafka import KafkaProducer
import random

# Configuration
KAFKA_TOPIC = "stock-ticks"
KAFKA_SERVER = "localhost:9092"
TICKERS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA"]

def get_stock_data():
    # Fetch real-time data (1 minute interval)
    data = yf.download(tickers=TICKERS, period="1d", interval="1m", group_by='ticker', progress=False)
    messages = []
    
    # Simulate "streaming" by taking the latest close and adding slight noise
    # (In production, you would use a real WebSocket API)
    timestamp = int(time.time())
    
    for ticker in TICKERS:
        try:
            # Get latest available price
            price = data[ticker]['Close'].iloc[-1]
            # Add random fluctuation to simulate live ticks if market is closed
            fluctuation = random.uniform(0.999, 1.001)
            current_price = round(float(price) * fluctuation, 2)
            
            record = {
                "ticker": ticker,
                "price": current_price,
                "timestamp": timestamp,
                "source": "yfinance"
            }
            messages.append(record)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            
    return messages

def run_producer():
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    print(f"🚀 Starting Producer to topic: {KAFKA_TOPIC}")
    
    while True:
        records = get_stock_data()
        for record in records:
            print(f"Sending: {record}")
            producer.send(KAFKA_TOPIC, record)
        
        producer.flush()
        time.sleep(2) # Wait 2 seconds between ticks

if __name__ == "__main__":
    run_producer()