import boto3
import random
from datetime import datetime, timedelta

# Configure the boto3 DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your AWS region
table_name = 'I-sole-device-data'  # Replace with your table name
table = dynamodb.Table(table_name)

# Function to generate fake data
def generate_fake_data(username, num_records):
    current_time = datetime.now()

    for _ in range(num_records):
        # Generate a fake glucose value between 100 and 200
        glucose_value = random.randint(100, 200)

        # Generate a timestamp
        timestamp = current_time.isoformat()

        # Create the item to insert into DynamoDB
        item = {
            'username': username,
            'timestamp': timestamp,
            'glucose_value': glucose_value
        }

        # Insert the item into the DynamoDB table
        table.put_item(Item=item)

        # Decrement the current time by a random number of minutes
        current_time -= timedelta(minutes=random.randint(1, 60))

# Example usage
username = 'testuser'  # Replace with your desired username
num_records = 100  # Number of records to insert

generate_fake_data(username, num_records)
print(f'Inserted {num_records} records for username: {username}')
