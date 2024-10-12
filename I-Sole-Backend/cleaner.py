import boto3
from faker import Faker
from decimal import Decimal
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('I-sole-users')  # Assuming 'I-sole-users' is your DynamoDB table for users

def delete_items_with_allergies():
    # Scan the table to find items with 'allergies' attribute
    response = table.scan(
        FilterExpression='attribute_exists(created_at)'
    )
    
    # Delete each item found
    for item in response['Items']:
        print(f"Deleting item with ID: {item['username']}")
        table.delete_item(
            Key={
                'username': item['username']
            }
        )
    
    print("Deletion of items with 'allergies' attribute completed.")

if __name__ == "__main__":
    delete_items_with_allergies()