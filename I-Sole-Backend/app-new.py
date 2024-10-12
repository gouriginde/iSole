import base64
import firebase_admin
from firebase_admin import auth, credentials, firestore, initialize_app
from flask import Flask, Blueprint, request, jsonify, render_template, redirect, url_for, send_file, Response
from flask_cors import CORS
import json
import pyrebase
from datetime import datetime, timezone
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Pause
import urllib.parse
import random
import bcrypt
import pytz
import tzlocal
import time
import statistics
import pandas as pd
import numpy as np
from keras.models import load_model
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pytz
from matplotlib.figure import Figure
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()



"""
This is the backend code for the I-Sole web application currently hosted on https://i-sole.site/.

The functionalities this backend supports are:

1. Authetication for login/signup
2. Thread-like chatting functionality
3. User Twilio to make emergency calls to patient's notifiers
4. Generates and returns patient's data analytics for Dashboard
5. Retrieve and store data in Firebase Database (NoSQL)
"""

"""App Config Setup"""

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": ["https://zeeshansalim1234.github.io"]}})
CORS(app, resources={r"/*": {"origins": "*"}})

cred = credentials.Certificate("i-sole-111bc-firebase-adminsdk-f1xl8-49b2e90098.json")
firebase_admin.initialize_app(cred)
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

db=firestore.client()
client = Client(account_sid, auth_token)

"""Setup Flask Endpoints"""

@app.route('/initialize_counter', methods=['POST'])
def initialize_counter():
    # This is necessary to keep track of the number of active threads in the chat section
    data = request.json
    username = data['username']
    initialize_user_thread_counter(username)
    return jsonify({"success": True})

@app.route('/signup', methods=['POST'])
def signup():
    try:
        # Parse the incoming data from the signup form
        signup_data = request.json
        username = signup_data['username']
        email = signup_data['email']
        full_name = signup_data['fullName']
        role = signup_data['role']
        password = signup_data['password']  # Be careful with handling passwords
        patient_id = signup_data.get('patientID', None)  # Optional field

         # Check if the role is 'Patient' and generate a unique patientID
        if role == 'Patient':
            patient_id = generate_unique_patient_id()
            update_id_map(patient_id, username)

        if role == 'Doctor': # add this doct as `myDoctor` for the patient profile
            add_doctor(get_username_from_patient_id(patient_id), username)

        # Create a reference to the Firestore document
        user_ref = db.collection('users').document(username)

        # Create a new document with the provided data
        user_ref.set({
            'email': email,
            'fullName': full_name,
            'username': username,
            'role': role,
            'password': password,  # Consider hashing the password
            'patientID': patient_id
        })

        user_data = user_ref.get().to_dict()

        return jsonify({"success": True, "message": "User created successfully", 'user_data': user_data}), 201

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/signin', methods=['POST'])
def signin():
    try:
        # Parse the incoming data from the sign-in form
        signin_data = request.json
        username = signin_data['username']
        password = signin_data['password']

        print(username)
        print(password)

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Attempt to get the document
        user_doc = user_ref.get()

        # Check if the document exists and if the password matches
        if user_doc.exists:
            user_data = user_doc.to_dict()
            if user_data['password'] == password:  # Consider using hashed passwords in production
                # Authentication successful
                return jsonify({"success": True, "message": "User signed in successfully", "user_data": user_data}), 200
            else:
                # Authentication failed
                return jsonify({"success": False, "message": "Incorrect password"}), 401
        else:
            # User not found
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    


@app.route('/get_username_by_patient_id/<patient_id>', methods=['GET'])
def get_username_by_patient_id(patient_id):
    try:
        # Retrieve the username mapped to the patient_id
        username = get_username_from_patient_id(patient_id)
        if username:
            return jsonify({"success": True, "username": username}), 200
        else:
            return jsonify({"success": False, "message": "Username not found for the given patient ID"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/start_new_thread', methods=['POST'])
def start_thread():
    # Initializes a new thread to Firebase DB
    data = request.json
    username = data['username']
    sender = data['sender']
    message = data['message']
    start_new_thread_with_message(username, message, sender)
    return jsonify({"success": True})

@app.route('/add_message', methods=['POST'])
def add_message():
    # Appends a message to existing thread in Firebase DB
    data = request.json
    username = data['username']
    index = data['index']
    message = data['message']
    sender = data['sender']
    add_message_to_conversation(username, index, message, sender)
    return jsonify({"success": True})

@app.route('/get_all_conversations/<username>', methods=['GET'])
def get_all(username):
    # Returns all threads for the specific user
    conversations = get_all_conversations(username)
    return jsonify(conversations)

@app.route('/get_one_conversation/<username>/<int:index>', methods=['GET'])
def get_one(username, index):
    # Returns 1 thread for which 'index' is passed, for the provided 'username'
    conversation = get_one_conversation(username, index)
    if conversation is not None:
        return jsonify(conversation)
    else:
        return jsonify({"error": "Conversation not found"}), 404


@app.route('/add_contact', methods=['POST'])
def add_contact():
    # Stores a new emergency contact for the current user in the Firebase DB
    try:
        # Parse the request data
        data = request.get_json()
        username = data['username']  # Make sure to send 'username' in your request payload
        new_contact = data['newContact']
        contact_info = {
            'name': new_contact['contactName'],
            'relationship': new_contact['relationship'],
            'phone_number': new_contact['phoneNumber'],
            'email': new_contact.get('email', None),  # Optional field
            'glucose_level_alert': new_contact['glucoseAlert'],
            'medication_reminder': new_contact['medicationReminder']
        }
        
        # Add a new contact document to the 'contacts' subcollection
        contact_ref = db.collection('users').document(username).collection('contacts').document()
        contact_ref.set(contact_info)
        
        # Return success response
        return jsonify({"success": True}), 200
    
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/delete_contact', methods=['POST'])
def delete_contact():
    # Deletes an existing emergency contact for the current user from the Firebase DB
    try:
        # Parse the request data
        data = request.get_json()
        username = data['username']  # Username to identify the user's document
        contact_name = data['contactName']  # Contact name to identify the contact document

        # Query the contacts subcollection for the user to find the contact document
        contacts_ref = db.collection('users').document(username).collection('contacts')
        contacts = contacts_ref.where('name', '==', contact_name).stream()

        # Delete the contact document(s)
        for contact in contacts:
            contact_ref = contacts_ref.document(contact.id)
            contact_ref.delete()

        # Return success response
        return jsonify({"success": True, "message": "Contact deleted successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {e}"}), 500


@app.route('/get_my_doctor/<username>', methods=['GET'])
def get_my_doctor(username):
    # Returns the 'doctorName' for the provided 'patientName'
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get the user document data
        user_doc = user_ref.get()

        # Check if the document exists and has the 'myDoctor' field
        if user_doc.exists:
            user_data = user_doc.to_dict()
            my_doctor = user_data.get('myDoctor')
            if my_doctor:
                print(my_doctor)
                return jsonify({"success": True, "myDoctor": my_doctor}), 200
            else:
                return jsonify({"success": False, "message": "myDoctor not found for the user"}), 404
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/get_all_contacts/<username>', methods=['GET'])
def get_all_contacts(username):
    # Returns all emergency contact for the provided username
    try:
        # Query the contacts subcollection for the given user
        contacts_ref = db.collection('users').document(username).collection('contacts')
        contacts_query = contacts_ref.stream()

        # Collect contact data from the documents
        contacts = []
        for contact_doc in contacts_query:
            contact_info = contact_doc.to_dict()
            contact_info['id'] = contact_doc.id  # Optionally include the document ID
            contacts.append(contact_info)

        # Return the contacts in the response
        return jsonify({"success": True, "contacts": contacts}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {e}"}), 500


@app.route("/make_call", methods=['GET', 'POST'])
def make_call():
    # This essentially sets up the config necessary for making a Twilio call via /voice

    # Get the 'to' phone number and the message from URL parameters
    if request.method == 'POST':
        data = request.json
        to_number = data.get('to')
        message = data.get('message', 'This is a default message')
    else:
        to_number = request.values.get('to')
        encoded_message = request.values.get('message', 'This is a default message')
        message = urllib.parse.unquote(encoded_message)

    print('Hello World')

    # Create a callback URL for the voice response
    callback_url = "https://i-sole-backend.com/voice?message=" + urllib.parse.quote(message)

    # Make the call using Twilio client
    try:
        call = client.calls.create(
            to=to_number,
            from_="+18254351557",
            url=callback_url,
            record=True
        )
        return f"Call initiated. SID: {call.sid}"
    except Exception as e:
        return f"Error: {e}"

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    # Leverages Twilio API to call patient's emergency contact

    # Get the message from the URL parameter
    message = request.values.get('message', 'This is a default message')
    
    # Create a VoiceResponse object
    response = VoiceResponse()

    # Split the message by lines and process each line
    for line in message.split('\n'):
        response.say(line, voice='Polly.Joanna-Neural', language='en-US')
        if line.strip().endswith('?'):
            response.append(Pause(length=3))

    # Return the TwiML as a string
    return Response(str(response), mimetype='text/xml')


@app.route('/add_pressure_value/<username>', methods=['POST'])
def add_pressure_value(username):
    try:
        # Get pressure value from request
        pressure_value1 = request.json.get('p1')
        pressure_value2 = request.json.get('p2')
        pressure_value3 = request.json.get('p3')
        pressure_value4 = request.json.get('p4')
        pressure_value5 = request.json.get('p5')
        pressure_value6 = request.json.get('p6')

        # Ensure pressure value is provided
        if pressure_value1 is None:
            return jsonify({"success": False, "message": "Pressure value not provided"}), 400

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Add pressure value to user's pressureData collection
        user_ref.collection('pressureData').add({
            'p1': pressure_value1,
            'p2': pressure_value2,
            'p3': pressure_value3,
            'p4': pressure_value4,
            'p5': pressure_value5,
            'p6': pressure_value6,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return jsonify({"success": True, "message": "Pressure value added successfully"}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/get_pressure_data/<username>', methods=['GET'])
def get_pressure_data(username):
    try:
        # Get start and end timestamps from query parameters
        start_timestamp_str = request.args.get('start')
        end_timestamp_str = request.args.get('end')

        # Convert timestamps to datetime objects
        start_timestamp = datetime.fromisoformat(start_timestamp_str)
        end_timestamp = datetime.fromisoformat(end_timestamp_str)

        # Convert datetime objects to UTC time
        # utc_timezone = pytz.utc
        # start_timestamp_utc = start_timestamp.astimezone(utc_timezone)
        # end_timestamp_utc = end_timestamp.astimezone(utc_timezone)

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get pressure data collection for the user
        pressure_data_ref = user_ref.collection('pressureData')

        # Query pressure data collection within the specified time range
        pressure_data_docs = pressure_data_ref.where('timestamp', '>=', start_timestamp_utc)\
                                              .where('timestamp', '<=', end_timestamp_utc)\
                                              .order_by('timestamp')\
                                              .get()

        pressure_data = []
        for doc in pressure_data_docs:
            pressure_data.append({
                'p1': doc.get('p1'),
                'p2': doc.get('p2'),
                'p3': doc.get('p3'),
                'p4': doc.get('p4'),
                'p5': doc.get('p5'),
                'p6': doc.get('p6'),
                'timestamp': doc.get('timestamp')
            })

        return jsonify({"success": True, "pressureData": pressure_data}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_average_pressure/<username>', methods=['GET'])
def get_average_pressure(username):
    try:
        # Get start and end timestamps from query parameters
        start_timestamp_str = request.args.get('start')
        end_timestamp_str = request.args.get('end')
        # Get the region from query parameters
        foot_region = request.args.get('footRegion')

        # Convert timestamps to datetime objects
        start_timestamp = datetime.fromisoformat(start_timestamp_str)
        end_timestamp = datetime.fromisoformat(end_timestamp_str)

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get pressure data collection for the user
        pressure_data_ref = user_ref.collection('pressureData')

        # Query pressure data collection within the specified time range
        pressure_data_docs = pressure_data_ref.where('timestamp', '>=', start_timestamp)\
                                              .where('timestamp', '<=', end_timestamp)\
                                              .order_by('timestamp')\
                                              .get()

        pressure_data = []
        for doc in pressure_data_docs:
            pressure_data.append({
                'p1': doc.get('p1'),
                'p2': doc.get('p2'),
                'p3': doc.get('p3'),
                'p4': doc.get('p4'),
                'p5': doc.get('p5'),
                'p6': doc.get('p6'),
                'timestamp': doc.get('timestamp')
        })

        # Extract all values for specified region
        p_values = []
        for pressure in pressure_data:
            p_values.append(pressure[foot_region])
        
        if(len(p_values) == 0):
            average_pressure = 0
            diabetic_ulceration_risk = 'Unknown'
        else:
            # Calculate the average of p_values and round it to 2 decimal places
            average_pressure = round(statistics.mean(p_values), 2)
            if(average_pressure <= 200):
                diabetic_ulceration_risk = 'Low'
            elif (average_pressure > 200):
                diabetic_ulceration_risk = 'High'

        return jsonify({"success": True, "averagePressure": average_pressure, "diabeticUlcerationRisk": diabetic_ulceration_risk}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/add_glucose_value/<username>', methods=['POST'])
def add_glucose_value(username):
    try:
        # Get glucose value from request
        glucose_value = request.json.get('glucose')

        # Ensure glucose value is provided
        if glucose_value is None:
            return jsonify({"success": False, "message": "Glucose value not provided"}), 400

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Add glucose value to user's glucoseData collection
        user_ref.collection('glucoseData').add({
            'glucose': glucose_value,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return jsonify({"success": True, "message": "Glucose value added successfully"}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/get_glucose_data/<username>', methods=['GET'])
def get_glucose_data(username):
    try:
        # Get start and end timestamps from query parameters
        start_timestamp_str = request.args.get('start')
        end_timestamp_str = request.args.get('end')

        # Convert timestamps to datetime objects
        start_timestamp = datetime.fromisoformat(start_timestamp_str)
        end_timestamp = datetime.fromisoformat(end_timestamp_str)

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get glucose data collection for the user
        glucose_data_ref = user_ref.collection('glucoseData')

        # Query glucose data collection within the specified time range
        glucose_data_docs = glucose_data_ref.where('timestamp', '>=', start_timestamp)\
                                              .where('timestamp', '<=', end_timestamp)\
                                              .order_by('timestamp')\
                                              .get()

        glucose_data = []
        for doc in glucose_data_docs:
            glucose_data.append({
                'glucose': doc.get('glucose'),
                'timestamp': doc.get('timestamp')
            })

        return jsonify({"success": True, "glucoseData": glucose_data}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_latest_glucose/<username>', methods=['GET', 'POST'])
def get_latest_glucose(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get glucose data collection for the user
        glucose_data_ref = user_ref.collection('glucoseData')

        # Query glucose data collection for the most recent entry
        latest_glucose_doc = glucose_data_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()

        sweat_glucose = round(latest_glucose_doc[0].get('glucose'), 2)
        blood_glucose = round(calculate_blood_glucose(sweat_glucose), 2)

        return jsonify({"success": True, "sweat_glucose": sweat_glucose, "blood_glucose": blood_glucose}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/add_meal/<username>', methods=['POST'])
def add_meal(username):
    try:
        # Get meal data from request
        meal_data = request.json

        # Ensure required fields are provided
        if 'meal_type' not in meal_data or 'meal_description' not in meal_data:
            return jsonify({"success": False, "message": "Meal data incomplete"}), 400

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Add meal data to user's meals collection
        user_ref.collection('meals').add({
            'meal_type': meal_data['meal_type'],
            'meal_description': meal_data['meal_description'],
            'carbohydrate_intake': meal_data['carbohydrate_intake'],
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return jsonify({"success": True, "message": "Meal added successfully"}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/get_meals/<username>', methods=['GET'])
def get_meals(username):
    try:
        # Get start and end timestamps from query parameters
        start_timestamp_str = request.args.get('start')
        end_timestamp_str = request.args.get('end')

        # Convert timestamps to datetime objects
        start_timestamp = datetime.fromisoformat(start_timestamp_str)
        end_timestamp = datetime.fromisoformat(end_timestamp_str)

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get meals collection for the user
        meals_ref = user_ref.collection('meals')

        # Query meals collection within the specified time range
        meals_docs = meals_ref.where('timestamp', '>=', start_timestamp)\
                              .where('timestamp', '<=', end_timestamp)\
                              .order_by('timestamp', direction='DESCENDING')\
                              .limit(10)\
                              .get()

        meals_data = []
        for doc in meals_docs:
            meals_data.append({
                'meal_type': doc.get('meal_type'),
                'timestamp': doc.get('timestamp'),
                'meal_description': doc.get('meal_description')
            })

        return jsonify({"success": True, "mealsData": meals_data}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route('/add_blood_glucose_level', methods=['POST'])
def add_blood_glucose_level():
    try:
        # Parse the request data
        username = request.json.get('username')
        bloodGlucoseLevel = request.json.get('bloodGlucoseLevel')
        
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        
        if personal_info_data:
           personal_metrics_ref.update({'blood_glucose_level': bloodGlucoseLevel})
           # Return success response
           return jsonify({"success": True}), 200

        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
        
@app.route('/get_blood_glucose_level/<username>', methods=['GET'])
def get_blood_glucose_level(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        # Get the user document data
        user_doc = user_ref.get()
        # Check if the document exists
        if user_doc.exists:
            # Get specific field from user document data
            user_data = user_doc.to_dict()
            blood_glucose_level = user_data.get('blood_glucose_level')
            return jsonify({"success": True, "data": {"blood_glucose_level": blood_glucose_level}}), 200
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/update_predicted_hypoglycemia', methods=['POST'])
def update_predicted_hypoglycemia():
    try:
        # Parse the request data
        username = request.json.get('username')
        predicted_hypoglycemia = request.json.get('predicted_hypoglycemia')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'predicted_hypoglycemia': predicted_hypoglycemia})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/get_predicted_hypoglycemia/<username>', methods=['GET'])
def get_predicted_hypoglycemia(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        # Get the user document data
        user_doc = user_ref.get()
        # Check if the document exists
        if user_doc.exists:
            # Get specific field from user document data
            user_data = user_doc.to_dict()
            predicted_hypoglycemia = user_data.get('predicted_hypoglycemia')
            return jsonify({"success": True, "data": {"predicted_hypoglycemia": predicted_hypoglycemia}}), 200
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_predicted_hyperglycemia', methods=['POST'])
def update_predicted_hyperglycemia():
    try:
        # Parse the request data
        username = request.json.get('username')
        predicted_hyperglycemia = request.json.get('predicted_hyperglycemia')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'predicted_hyperglycemia': predicted_hyperglycemia})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/get_predicted_hyperglycemia/<username>', methods=['GET'])
def get_predicted_hyperglycemia(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        # Get the user document data
        user_doc = user_ref.get()
        # Check if the document exists
        if user_doc.exists:
            # Get specific field from user document data
            user_data = user_doc.to_dict()
            predicted_hyperglycemia = user_data.get('predicted_hyperglycemia')
            return jsonify({"success": True, "data": {"predicted_hyperglycemia": predicted_hyperglycemia}}), 200
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_height', methods=['POST'])
def update_height():
    try:
        # Parse the request data
        username = request.json.get('username')
        height = request.json.get('height')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'height': height})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_weight', methods=['POST'])
def update_weight():
    try:
        # Parse the request data
        username = request.json.get('username')
        weight = request.json.get('weight')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'weight': weight})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_finger_stick_value', methods=['POST'])
def update_finger_stick_value():
    try:
        # Parse the request data
        username = request.json.get('username')
        finger_stick_value = request.json.get('finger_stick_value')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'finger_stick_value': finger_stick_value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_basal_value', methods=['POST'])
def update_basal_value():
    try:
        # Parse the request data
        username = request.json.get('username')
        basal_value = request.json.get('basal_value')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'basal_value': basal_value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_basis_gsr_value', methods=['POST'])
def update_basis_gsr_value():
    try:
        # Parse the request data
        username = request.json.get('username')
        basis_gsr_value = request.json.get('basis_gsr_value')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'basis_gsr_value': basis_gsr_value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_basis_skin_temperature_value', methods=['POST'])
def update_basis_skin_temperature_value():
    try:
        # Parse the request data
        username = request.json.get('username')
        basis_skin_temperature_value = request.json.get('basis_skin_temperature_value')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'basis_skin_temperature_value': basis_skin_temperature_value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_bolus_dose', methods=['POST'])
def update_bolus_dose():
    try:
        # Parse the request data
        username = request.json.get('username')
        bolus_dose = request.json.get('bolus_dose')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'bolus_dose': bolus_dose})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
    
@app.route('/update_insulin_dosage', methods=['POST'])
def update_insulin_dosage():
    try:
        # Parse the request data
        username = request.json.get('username')
        insulinDosage = request.json.get('insulinDosage')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'insulin_dosage': insulinDosage})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_allergies', methods=['POST'])
def update_allergies():
    try:
        # Parse the request data
        username = request.json.get('username')
        allergies = request.json.get('allergies')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'allergies': allergies})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_insulin_type', methods=['POST'])
def update_insulin_type():
    try:
        # Parse the request data
        username = request.json.get('username')
        insulin_type = request.json.get('insulin_type')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'insulin_type': insulin_type})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_physical_activity', methods=['POST'])
def update_physical_activity():
    try:
        # Parse the request data
        username = request.json.get('username')
        physical_activity = request.json.get('physical_activity')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'physical_activity': physical_activity})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_activity_intensity', methods=['POST'])
def update_activity_intensity():
    try:
        # Parse the request data
        username = request.json.get('username')
        activity_intensity = request.json.get('activity_intensity')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'activity_intensity': activity_intensity})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_activity_duration', methods=['POST'])
def update_activity_duration():
    try:
        # Parse the request data
        username = request.json.get('username')
        activity_duration = request.json.get('activity_duration')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'activity_duration': activity_duration})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_stress_level', methods=['POST'])
def update_stress_level():
    try:
        # Parse the request data
        username = request.json.get('username')
        stress_level = request.json.get('stress_level')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'stress_level': stress_level})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_illness', methods=['POST'])
def update_illness():
    try:
        # Parse the request data
        username = request.json.get('username')
        illness = request.json.get('illness')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'illness': illness})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_hormonal_changes', methods=['POST'])
def update_hormonal_changes():
    try:
        # Parse the request data
        username = request.json.get('username')
        hormonal_changes = request.json.get('hormonal_changes')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'hormonal_changes': hormonal_changes})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_alcohol_consumption', methods=['POST'])
def update_alcohol_consumption():
    try:
        # Parse the request data
        username = request.json.get('username')
        alcohol_consumption = request.json.get('alcohol_consumption')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'alcohol_consumption': alcohol_consumption})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_medication', methods=['POST'])
def update_medication():
    try:
        # Parse the request data
        username = request.json.get('username')
        medication = request.json.get('medication')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'medication': medication})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_medication_dosage', methods=['POST'])
def update_medication_dosage():
    try:
        # Parse the request data
        username = request.json.get('username')
        medication_dosage = request.json.get('medication_dosage')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'medication_dosage': medication_dosage})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_weather_conditions', methods=['POST'])
def update_weather_conditions():
    try:
        # Parse the request data
        username = request.json.get('username')
        weather_conditions = request.json.get('weather_conditions')
        # Check if the document exists
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        personal_info_data = personal_metrics_ref.get().to_dict()
        if personal_info_data:
           personal_metrics_ref.update({'weather_conditions': weather_conditions})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document personal_info does not exist for user: " + username}), 404  
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_personal_metrics/<username>', methods=['GET', 'POST'])
def get_personal_metrics(username):
    try:
        # Reference to the Firestore document of the user
        personal_metrics_ref = db.collection('users').document(username).collection('personal-metrics').document('personal-info')
        # Get the user document data
        personal_metrics_doc = personal_metrics_ref.get()
        # Check if the document exists
        if personal_metrics_doc.exists:
            personal_data = personal_metrics_doc.to_dict()
            return jsonify({"success": True, "data": personal_data}), 200  # Set success to True and include data
        else:
            return jsonify({"success": False, "message": "Personal metrics not found"}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/update_name', methods=['POST'])
def update_name():
    try:
        # Parse the request data
        username = request.json.get('username')
        name = request.json.get('name')
        
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        
        if profile_data:
           users_ref.update({'fullName': name})
           # Return success response
           return jsonify({"success": True}), 200

        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_email', methods=['POST'])
def update_email():
    try:
        # Parse the request data
        username = request.json.get('username')
        email = request.json.get('email')
        
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        
        if profile_data:
           users_ref.update({'email': email})
           # Return success response
           return jsonify({"success": True}), 200

        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_phone_number', methods=['POST'])
def update_phone_number():
    try:
        # Parse the request data
        username = request.json.get('username')
        phoneNumber = request.json.get('phoneNumber')
        
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        
        if profile_data:
           users_ref.update({'phoneNumber': phoneNumber})
           # Return success response
           return jsonify({"success": True}), 200

        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/update_date_of_birth', methods=['POST'])
def update_date_of_birth():
    try:
        # Parse the request data
        username = request.json.get('username')
        dateOfBirth = request.json.get('dateOfBirth')
        
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        
        if profile_data:
           users_ref.update({'dateOfBirth': dateOfBirth})
           # Return success response
           return jsonify({"success": True}), 200

        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_emergency_contact', methods=['POST'])
def update_emergency_contact():
    try:
        # Parse the request data
        username = request.json.get('username')
        emergencyContact = request.json.get('emergencyContact')
        
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        
        if profile_data:
           users_ref.update({'emergencyContact': emergencyContact})
           # Return success response
           return jsonify({"success": True}), 200

        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
        
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_profile_data/<username>', methods=['GET'])
def get_profile_data(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get the user document data
        user_doc = user_ref.get()

        # Check if the document exists
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return jsonify({"success": True, "data": user_data}), 200  # Set success to True and include data
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_view_activity', methods=['POST'])
def update_view_activity():
    try:
        # Parse the request data
        username = request.json.get('username')
        value = request.json.get('value')
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        if profile_data:
           users_ref.update({'view_activity': value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_view_activity/<username>', methods=['GET'])
def get_view_activity(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)
        # Get the user document data
        user_doc = user_ref.get()
        # Check if the document exists
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return jsonify({"success": True, "view_activity": user_data['view_activity']}), 200  # Set success to True and include data
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_view_meals', methods=['POST'])
def update_view_meals():
    try:
        # Parse the request data
        username = request.json.get('username')
        value = request.json.get('value')
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        if profile_data:
           users_ref.update({'view_meals': value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_view_meals/<username>', methods=['GET'])
def get_view_meals(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)
        # Get the user document data
        user_doc = user_ref.get()
        # Check if the document exists
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return jsonify({"success": True, "view_meals": user_data['view_meals']}), 200  # Set success to True and include data
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_view_feedback', methods=['POST'])
def update_view_feedback():
    try:
        # Parse the request data
        username = request.json.get('username')
        value = request.json.get('value')
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        if profile_data:
           users_ref.update({'view_feedback': value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_view_feedback/<username>', methods=['GET'])
def get_view_feedback(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)
        # Get the user document data
        user_doc = user_ref.get()
        # Check if the document exists
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return jsonify({"success": True, "view_feedback": user_data['view_feedback']}), 200  # Set success to True and include data
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_notifications', methods=['POST'])
def update_notifications():
    try:
        # Parse the request data
        username = request.json.get('username')
        value = request.json.get('value')
        # Check if the document exists
        users_ref = db.collection('users').document(username)
        profile_data = users_ref.get().to_dict()
        if profile_data:
           users_ref.update({'notifications': value})
           # Return success response
           return jsonify({"success": True}), 200
        else:
            # Document doesn't exist, return error response
            return jsonify({"success": False, "message": "Document does not exist for user: " + username}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/get_notifications/<username>', methods=['GET'])
def get_notifications(username):
    try:
        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)
        # Get the user document data
        user_doc = user_ref.get()
        # Check if the document exists
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return jsonify({"success": True, "notifications": user_data['notifications']}), 200  # Set success to True and include data
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"success": False, "message": str(e)}), 500
    

# """Helper Methods"""

    
@app.route('/plot_pressure', methods=['GET'])
def serve_plot():
    username = request.args.get('username')
    start_timestamp = request.args.get('start_timestamp')
    end_timestamp = request.args.get('end_timestamp')
    region = request.args.get('region')

    #"2024-01-01T00:00:00"

    # Directly fetch the pressure data using the internal function
    print("serve_plot called\n\n")
    pressure_data = fetch_pressure_data_internal(username, start_timestamp, end_timestamp, region)
    # print("My data: \n\n\n",pressure_data)

    # Extracting 'p4' values
    print("region: ",region)
    print()

    region_values = [data[region] for data in pressure_data if region in data]
    print("region values: ", region_values)

    # If there are more than 50 values, keep only the last 50
    if len(region_values) > 50:
        region_values = region_values[-50:]

    print("region values 50: ", region_values)

    # Convert all values to floats
    region_values_float = [float(value) for value in region_values]

    if isinstance(region_values_float, list):
        # Plot the pressure data and get the image buffer
        image_buffer = plot_pressure(region_values_float)
        return send_file(image_buffer, mimetype='image/png')
    else:
        return jsonify({"success": False, "message": "Failed to fetch pressure data"}), 500
    

"""Helper Methods"""

def plot_pressure(training_data):
    plt.figure(figsize=(12, 7), facecolor='#1b2130')
    ax = plt.axes()
    ax.set_facecolor('#1b2130')


    timestamps = [x * 5 for x in range(50)]
    data_to_plot = training_data + [None] * (50 - len(training_data))

    if data_to_plot:
        plt.plot(timestamps, data_to_plot, label='Insole Recorded Data', color='#007bff', marker='o', markersize=12, linewidth=3, markeredgewidth=2, markeredgecolor='white')
        valid_indices = [i for i, v in enumerate(data_to_plot) if v is not None]
        if valid_indices:
            plt.fill_between(timestamps[:valid_indices[-1]+1], data_to_plot[:valid_indices[-1]+1], color='#007bff', alpha=0.075)

    plt.xticks(timestamps, [str(ts) for ts in timestamps], rotation=45, color='white', fontsize=12)
    plt.yticks(color='white', fontsize=12)

    if training_data:
        y_min, y_max = min(training_data), max(training_data)
        y_range = y_max - y_min
        plt.ylim(y_min - 0.05 * y_range, y_max + 0.3 * y_range)

    plt.xlabel('Time (seconds)', color='white', fontsize=16, labelpad=20, fontweight='600')
    plt.ylabel('Pressure Value (kPa)', color='white', fontsize=16, labelpad=20, fontweight='600')
    # Create the legend
    legend = plt.legend(facecolor='#1b2130', edgecolor='white', fontsize=16, loc='upper left')

    # Set the color of all the legend text to white
    for text in legend.get_texts():
        text.set_color('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('white')
    plt.grid(color='gray', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=ax.get_facecolor())
    plt.close()
    buf.seek(0)
    return buf

def fetch_pressure_data_internal(username, start_timestamp_str, end_timestamp_str, region):
    try:
        # Convert string timestamps to datetime objects
        start_timestamp = datetime.fromisoformat(start_timestamp_str)
        end_timestamp = datetime.fromisoformat(end_timestamp_str)

        # Reference to the Firestore document of the user
        user_ref = db.collection('users').document(username)

        # Get pressure data collection for the user
        pressure_data_ref = user_ref.collection('pressureData')

        print('Hello')

        # Query pressure data collection within the specified time range
        pressure_data_docs = pressure_data_ref.where('timestamp', '>=', start_timestamp)\
                                              .where('timestamp', '<=', end_timestamp)\
                                              .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                                              .limit(50)\
                                              .get()
        
        print('Bye')

        # Extract pressure data from the documents for the specified region
        pressure_data = []
        for doc in pressure_data_docs:
            pressure_data.append({
                region: doc.get(region),  # Only get the region specified
                'timestamp': doc.get('timestamp')
            })

        return pressure_data  # Return the data directly

    except Exception as e:
        print(f"Error fetching pressure data: {e}")
        return []  # Return an empty list or handle the error as needed


def add_doctor(username, doctorName):
    # Reference to the Firestore document of the user
    user_ref = db.collection('users').document(username)

    # Update the user document to add the 'myDoctor' field
    user_ref.update({'myDoctor': doctorName})

def initialize_user_thread_counter(username): # need to call at creation of each account
    # Reference to the user's thread counter document
    counter_ref = db.collection('users').document(username).collection('feedback').document('thread_counter')
    
    # Set the initial value of the counter
    counter_ref.set({'last_thread_number': 0})


def generate_unique_patient_id():
    # Repeat until a unique ID is found
    while True:
        # Generate a random number for patientID
        patient_id = str(random.randint(10000, 99999))  # Adjust range as needed

        # Check if this patientID is already in use
        if not check_patient_id_exists(patient_id):
            return patient_id

def check_patient_id_exists(patient_id):
    # Query Firestore to check if the patientID already exists
    users_ref = db.collection('users')
    query = users_ref.where('patientID', '==', patient_id).limit(1).stream()
    return any(query)

def update_id_map(patient_id, username):
    """
    Update the idmap document in the system_data collection with the patient ID and username.
    """
    idmap_ref = db.collection('system_data').document('idmap')
    # Use a transaction to ensure atomicity
    @firestore.transactional
    def update_in_transaction(transaction, ref, pid, uname):
        snapshot = ref.get(transaction=transaction)
        if snapshot.exists:
            current_map = snapshot.to_dict()
            current_map[pid] = uname
        else:
            current_map = {pid: uname}
        transaction.set(ref, current_map)
    
    transaction = db.transaction()
    update_in_transaction(transaction, idmap_ref, patient_id, username)


def get_username_from_patient_id(patient_id):
    # Assuming you have a 'system_data' collection and an 'idmap' document
    idmap_ref = db.collection('system_data').document('idmap')
    idmap_doc = idmap_ref.get()
    if idmap_doc.exists:
        idmap = idmap_doc.to_dict()
        return idmap.get(patient_id)
    return None


@firestore.transactional
def increment_counter(transaction, counter_ref):
    snapshot = counter_ref.get(transaction=transaction)
    last_number = snapshot.get('last_thread_number')

    if last_number is None:
        last_number = 0
        transaction.set(counter_ref, {'last_thread_number': last_number})

    new_number = last_number + 1
    transaction.update(counter_ref, {'last_thread_number': new_number})
    return new_number

def start_new_thread_with_message(username, message, sender):
    counter_ref = db.collection('users').document(username).collection('feedback').document('thread_counter')
    new_thread_number = increment_counter(db.transaction(), counter_ref)

    new_thread = "thread" + str(new_thread_number)
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")

    message_data = {
        'message': message,
        'date': date_str,
        'time': time_str,
        'sender': sender
    }

    doc_ref = db.collection('users').document(username).collection('feedback').document(new_thread)
    doc_ref.set({'messages': [message_data]})


def add_message_to_conversation(username, index, message, sender):
    desired_thread = "thread" + str(index)
    # Get the current datetime
    now = datetime.now()
    # Format date and time (12-hour clock with AM/PM)
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")  # Format for 12-hour clock with AM/PM

    # Prepare the message data with separate date and time
    message_data = {
        'message': message,
        'date': date_str,
        'time': time_str,
        'sender': sender
    }

    # Get a reference to the document
    doc_ref = db.collection('users').document(username).collection('feedback').document(desired_thread)

    # Use set with merge=True to update if exists or create if not exists
    doc_ref.set({'messages': firestore.ArrayUnion([message_data])}, merge=True)

def get_all_conversations(username):
    # Array to hold the first message and count of each thread
    first_messages = []

    # Reference to the user's feedback collection
    feedback_ref = db.collection('users').document(username).collection('feedback')

    # Get all documents (threads) in the feedback collection
    threads = feedback_ref.stream()

    for thread in threads:
        # Get the thread data
        thread_data = thread.to_dict()

        # Check if 'messages' field exists and has at least one message
        if 'messages' in thread_data and thread_data['messages']:
            # Get the count of messages in the thread
            message_count = len(thread_data['messages'])

            # Create a new dict with the 0th message and the count
            first_message_with_count = {
                **thread_data['messages'][0],
                'count': message_count
            }

            # Append this new dict to the array
            first_messages.append(first_message_with_count)

    return first_messages

def get_one_conversation(username, index):
    # Construct the thread ID from the index
    desired_thread = "thread" + str(index)

    # Reference to the specific document (thread) in the user's feedback collection
    thread_ref = db.collection('users').document(username).collection('feedback').document(desired_thread)

    # Attempt to get the document
    thread_doc = thread_ref.get()

    # Check if the document exists and return the 'messages' array if it does
    if thread_doc.exists:
        thread_data = thread_doc.to_dict()
        return thread_data.get('messages', [])  # Return the messages array or an empty array if not found

    # Return None or an empty array if the document does not exist
    return None

def predict_single_entry(input_data):
    # Load the trained model and scaler objects
    model_path = '544_trained_model.h5'
    model = load_model(model_path)
    scaler_x_path = '544_scaler_x.pkl'
    scaler_y_path = '544_scaler_y.pkl'
    scaler_x = joblib.load(scaler_x_path)
    scaler_y = joblib.load(scaler_y_path)

    # Ensure input_data is a DataFrame with the expected columns
    if isinstance(input_data, pd.DataFrame) == False:
        raise ValueError("Input data must be a pandas DataFrame.")
    
    # Ensure the DataFrame has the expected structure
    expected_cols = ['glucose_level_value', 'finger_stick_value', 'basal_value', 'basis_gsr_value', 'basis_skin_temperature_value', 'bolus_dose']
    if not all(col in input_data.columns for col in expected_cols):
        raise ValueError("Input DataFrame does not contain the expected columns.")
    
    # Preprocess the input data
    X_input = input_data.apply(pd.to_numeric, errors='coerce').fillna(0)
    scaled_X_input = scaler_x.transform(X_input)
    scaled_X_input = np.reshape(scaled_X_input, (1, scaled_X_input.shape[0], scaled_X_input.shape[1]))
    
    # Make prediction
    prediction = model.predict(scaled_X_input, batch_size=1)
    scaled_prediction = scaler_y.inverse_transform(prediction)
    
    return scaled_prediction.flatten()[0]  # Return a single predicted value


def calculate_blood_glucose(sweat_glucose_umolL):
    BG_high = 300  # mg/dL
    BG_low = 50    # mg/dL
    SG_high_mgDL = 36   # mg/dL
    SG_low_mgDL = 10.8  # mg/dL

    # Calculate K
    K = (BG_high - BG_low) / (SG_high_mgDL - SG_low_mgDL)

    # Calculate Io
    Io = BG_low - K * SG_low_mgDL

    """
    Convert sweat glucose signal from µmol/L to estimated blood glucose level in mg/dL.
    """
    # Convert sweat glucose from µmol/L to mg/dL
    sweat_glucose_mgDL = sweat_glucose_umolL * 0.18

    # Calculate estimated blood glucose
    BG = K * sweat_glucose_mgDL + Io
    return BG

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5002)