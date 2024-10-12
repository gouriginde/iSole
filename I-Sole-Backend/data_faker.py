import threading
import boto3
import random
from datetime import datetime, timedelta
from decimal import Decimal
import time

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('I-sole-device-data')

def generate_random_pressure_data():
    return {
        'p1': Decimal(str(round(random.uniform(1.0, 5.0), 3))),
        'p2': Decimal(str(round(random.uniform(1.0, 5.0), 3))),
        'p3': Decimal(str(round(random.uniform(1.0, 5.0), 3))),
        'p4': Decimal(str(round(random.uniform(1.0, 5.0), 3))),
        'p5': Decimal(str(round(random.uniform(1.0, 5.0), 3))),
        'p6': Decimal(str(round(random.uniform(1.0, 5.0), 3)))
    }

def generate_random_glucose_value():
    return Decimal(str(round(random.uniform(100, 250), 2)))

def add_pressure_data(username):
    while getattr(threading.current_thread(), "do_run", True):
        # Generate current timestamp and format it as string
        timestamp = datetime.utcnow().isoformat(sep='T', timespec='microseconds')
        
        # Generate random pressure data
        pressure_data = generate_random_pressure_data()
        
        # Generate random glucose value
        glucose_value = generate_random_glucose_value()
        
        # Prepare the item to be inserted
        item = {
            'username': username,
            'timestamp': timestamp,
            'p_value': pressure_data,
            'glucose_value': glucose_value  # Add glucose_value field
        }
        
        # Put the item into the DynamoDB table
        table.put_item(Item=item)
        print(f"Inserted item with timestamp {timestamp} and glucose_value {glucose_value} in user: {username}")
        
        # Wait for 1 second before inserting the next record
        time.sleep(10)

if __name__ == "__main__":
    username = 'testuser'
    add_pressure_data(username)
