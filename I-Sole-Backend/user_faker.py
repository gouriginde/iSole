import boto3
from faker import Faker
from decimal import Decimal
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('I-sole-users')  # Assuming 'I-sole-users' is your DynamoDB table for users

# Initialize Faker instance
fake = Faker()

def generate_personal_metrics():
    return {
        'basal_value': Decimal(str(round(fake.random.uniform(1.0, 2.5), 2))),
        'basis_gsr_value': Decimal(str(round(fake.random.uniform(0.001, 0.01), 3))),
        'basis_skin_temperature_value': int(fake.random.randint(80, 100)),
        'bolus_dose': Decimal(str(round(fake.random.uniform(0.0, 10.0), 2))),
        'finger_stick_value': int(fake.random.randint(90, 120)),
        'height': Decimal(str(fake.random.uniform(4.5, 6.5))),  # Feet
        'weight': int(fake.random.randint(100, 250))  # Pounds
    }

def generate_fake_user():
    # Generate fake data
    username = fake.user_name()
    email = fake.email()
    password = fake.password()
    name = fake.name()
    personal_metrics = generate_personal_metrics()
    
    # Prepare item for DynamoDB
    item = {
        'username': username,
        'email': email,
        'password': password,
        'name': name,
        'personal_metrics': personal_metrics,
    }
    
    return item

def populate_dynamodb(num_users):
    for _ in range(num_users):
        user_item = generate_fake_user()
        
        # Put item into DynamoDB table
        table.put_item(Item=user_item)
        
        print(f"Inserted user with username '{user_item['username']}'")

if __name__ == "__main__":
    num_users = 10  # Adjust the number of users to create
    populate_dynamodb(num_users)