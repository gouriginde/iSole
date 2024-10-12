import boto3
from datetime import datetime, timedelta
import random

# Initialize a session using Amazon DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('I-sole-users')
device_data_table = dynamodb.Table('I-sole-device-data')

# Function to generate a random p_value
def generate_p_value():
    return {
        "p1": random.randint(100, 250),
        "p2": random.randint(100, 250),
        "p3": random.randint(100, 250),
        "p4": random.randint(100, 250),
        "p5": random.randint(100, 250),
        "p6": random.randint(100, 250)
    }

# Get the current time
now = datetime.utcnow()

# Generate 30 timestamps from now till the past 30 minutes
timestamps = [now - timedelta(minutes=i) for i in range(30)]

# Populate the table
for timestamp in timestamps:
    item = {
        "username": "testuser",
        "timestamp": timestamp.isoformat(),
        "p_value": generate_p_value()
    }
    device_data_table.put_item(Item=item)

print(f"Successfully populated 30 records in the I-sole-device-data table.")