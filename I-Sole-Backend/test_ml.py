import requests
import json

# The URL for the API endpoint
url = 'http://127.0.0.1:5000/plot-prediction'

# The data you want to send in your POST request
data = {
    "input_data": {
        "glucose_level_value": 170.16666666666666, 
        "finger_stick_value": 101.0, 
        "basal_value": 1.5, 
        "basis_gsr_value": 0.0724993103448275, 
        "basis_skin_temperature_value": 87.46172413793103, 
        "bolus_dose": 0.0
    }, 
    "hyperglycemia_threshold": 180, 
    "hypoglycemia_threshold": 100
}

# Convert the data to a JSON string
json_data = json.dumps(data)

# Set the content type to application/json
headers = {'Content-Type': 'application/json'}

# Make the POST request
response = requests.post(url, data=json_data, headers=headers)

# Assuming the response contains an image, save it to a file
if response.status_code == 200:
    with open('plot_result.png', 'wb') as f:
        f.write(response.content)
    print("Plot saved to plot_result.png")
else:
    print("Error:", response.status_code, response.text)
