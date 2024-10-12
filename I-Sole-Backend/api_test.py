import unittest
import requests
import json

class TestFlaskApi(unittest.TestCase):

    def test_signup_patient(self):
        url = "http://127.0.0.1:5000/signup"
        patient_data = {
            "username": "patientuser1",
            "email": "patient@example.com",
            "fullName": "John Doe",
            "role": "Patient",
            "password": "securepassword"
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(patient_data), headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('User created successfully', response.json()['message'])

    def test_get_username_by_patient_id(self):
        patient_id = '66373'
        url = f"http://127.0.0.1:5000/get_username_by_patient_id/{patient_id}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json().get('username'))

    def test_get_all_conversations(self):
        username = 'Zeeshan'
        url = f"http://127.0.0.1:5000/get_all_conversations/{username}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list) 

    def test_get_one_conversation(self):
        username = 'Zeeshan'
        index = 1 
        url = f"http://127.0.0.1:5000/get_one_conversation/{username}/{index}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())

    def test_add_contact(self):
        url = "http://127.0.0.1:5000/add_contact"
        data = {
            'username': 'Zeeshan',
            'newContact': {
                'contactName': 'John Doe',
                'relationship': 'Friend',
                'phoneNumber': '1234567890',
                'glucoseAlert': True,
                'medicationReminder': False
            }
        }
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())

    def test_delete_contact(self):
        url = "http://127.0.0.1:5000/delete_contact"
        data = {
            'username': 'Zeeshan',
            'contactName': 'John Doe'
        }
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Contact deleted successfully', response.json().get('message'))


if __name__ == "__main__":
    unittest.main()