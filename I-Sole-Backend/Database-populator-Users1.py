import boto3
import random
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('I-sole-users')

# Define list of possible values for categorical attributes
activity_intensity_values = ["Low", "Medium", "High"]
alcohol_consumption_values = ["Alcohol", "No Alcohol"]
allergies_values = ["Peanuts", "Shellfish", "Dairy", "Gluten", "Eggs", "Soy", "Fish", "Tree Nuts", "Wheat"]
hormonal_changes_values = ["Cortisol", "Other Hormonal Changes"]
illness_values = ["Fever", "No Illness"]
insulin_type_values = ["Bolus", "Basal", "Other Insulin Type"]
medication_values = ["Metformin", "Insulin", "Other Medication"]
physical_activity_values = ["None", "Light", "Moderate", "Vigorous"]
weather_conditions_values = ["Cold", "Hot", "Windy", "Sunny", "Rainy", "Snowy"]
stress_level_values = ["Low", "Moderate", "High"]
predicted_hypoglycemia_values = ["Sun, 25 Mar 2024 22:40:44 GMT","Tue, 26 Mar 2024 22:28:44 GMT","Mon, 20 Mar 2024 12:40:41 GMT"]

# Define range for numerical attributes
activity_duration_range = (10, 120)
basal_value_range = (5, 20)
basis_gsr_value_range = (10, 30)
basis_skin_temperature_value_range = (10, 30)
blood_glucose_level_range = (4, 10)
bolus_dose_range = (10, 50)
finger_stick_value_range = (5, 15)
height_range = (4, 7)
insulin_dosage_range = (50, 200)
medication_dosage_range = (20, 60)
weight_range = (30, 150)

# Add random data to each user
response = table.scan()
for item in response['Items']:
    username = item['username']
    # Add random data for each attribute
    table.update_item(
        Key={'username': username},
        UpdateExpression='SET ' +
                         'activity_duration = :ad, ' +
                         'activity_intensity = :ai, ' +
                         'alcohol_consumption = :ac, ' +
                         'allergies = :al, ' +
                         'basal_value = :bv, ' +
                         'basis_gsr_value = :bgv, ' +
                         'basis_skin_temperature_value = :bstv, ' +
                         'blood_glucose_level = :bgl, ' +
                         'bolus_dose = :bd, ' +
                         'finger_stick_value = :fv, ' +
                         'height = :h, ' +
                         'hormonal_changes = :hc, ' +
                         'illness = :il, ' +
                         'insulin_dosage = :id, ' +
                         'insulin_type = :it, ' +
                         'medication = :m, ' +
                         'medication_dosage = :md, ' +
                         'physical_activity = :pa, ' +
                         'predicted_hyperglycemia = :ph, ' +
                         'predicted_hypoglycemia = :phg, ' +
                         'stress_level = :sl, ' +
                         'weather_conditions = :wc, ' +
                         'weight = :w',
        ExpressionAttributeValues={
            ':ad': str(random.randint(*activity_duration_range)),
            ':ai': random.choice(activity_intensity_values),
            ':ac': random.choice(alcohol_consumption_values),
            ':al': random.choice(allergies_values),
            ':bv': str(random.randint(*basal_value_range)),
            ':bgv': str(random.randint(*basis_gsr_value_range)),
            ':bstv': str(random.randint(*basis_skin_temperature_value_range)),
            ':bgl': str(random.uniform(*blood_glucose_level_range)),
            ':bd': str(random.randint(*bolus_dose_range)),
            ':fv': str(random.randint(*finger_stick_value_range)),
            ':h': str(random.randint(*height_range)),
            ':hc': random.choice(hormonal_changes_values),
            ':il': random.choice(illness_values),
            ':id': str(random.randint(*insulin_dosage_range)),
            ':it': random.choice(insulin_type_values),
            ':m': random.choice(medication_values),
            ':md': str(random.randint(*medication_dosage_range)),
            ':pa': random.choice(physical_activity_values),
            ':ph': str(datetime.now()),
            ':phg': random.choice(predicted_hypoglycemia_values),
            ':sl': random.choice(stress_level_values),
            ':wc': random.choice(weather_conditions_values),
            ':w': str(random.randint(*weight_range))
        }
    )
