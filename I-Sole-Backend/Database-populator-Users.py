import boto3
from faker import Faker
import random
from decimal import Decimal

# Initialize Faker and boto3 client
fake = Faker()
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Specify your table name
table_name = 'I-sole-users'  # Change this to your actual table name
table = dynamodb.Table(table_name)

# Function to generate unique username
def generate_unique_username(existing_usernames):
    while True:
        username = fake.user_name()
        if username not in existing_usernames:
            return username

# Function to generate random user data
def generate_user_data(existing_usernames):
    name = fake.name()
    username = generate_unique_username(existing_usernames)
    email = fake.email()
    patient_id = fake.uuid4()
    role = random.choice(['Patient', 'Doctor'])
    date_of_birth = fake.date_of_birth(minimum_age=10, maximum_age=90).strftime("%Y-%m-%d")
    height = Decimal(random.uniform(4.5, 6.5))

    return {
        'name': name,
        'username': username,
        'email': email,
        'patient_id': patient_id,
        'role': role,
        'date_of_birth': date_of_birth,
        'height': round(height, 2)
    }

# Generate and insert data for N users
N = 20  # Change this to the number of users you want to generate
existing_usernames = set()

for _ in range(N):
    user_data = generate_user_data(existing_usernames)
    existing_usernames.add(user_data['username'])
    table.put_item(Item=user_data)
    print(f"Inserted user: {user_data}")

print(f"Successfully inserted {N} users into the '{table_name}' table.")
