import boto3
import random
from datetime import datetime, timedelta

# Assume you have already initialized your DynamoDB resource and tables
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('I-sole-users')
device_data_table = dynamodb.Table('I-sole-device-data')

# Get all usernames from the users table
response = users_table.scan()
usernames = [user['username'] for user in response['Items']]

# Generate and insert data for each user
for username in usernames:
    for _ in range(10):
        # Generate a random timestamp within the last 30 days
        random_date = datetime.now() - timedelta(days=random.randint(0, 30))
        timestamp = random_date.strftime('%B %d, %Y at %I:%M:%S %p UTC-6')

        # Generate a random glucose level between 80 and 130
        glucose_level = random.randint(80, 130)

        # Insert data into the device data table
        device_data_table.put_item(
            Item={
                'username': username,
                'timestamp': timestamp,
                'glucose_level': glucose_level
            }
        )