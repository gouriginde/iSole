import pandas as pd
import numpy as np
from keras.models import load_model
import joblib
import tensorflow as tf
print(tf.__version__)

def predict_single_entry(input_data):
    # Load the trained model and scaler objects
    model_path = '544_trained_model.h5'
    model = load_model(model_path)
    scaler_x_path = '544_scaler_x.pkl'
    scaler_y_path = '544_scaler_y.pkl'
    scaler_x = joblib.load(scaler_x_path)
    scaler_y = joblib.load(scaler_y_path)

    # Ensure input_data is a DataFrame with the expected columns
    if not isinstance(input_data, pd.DataFrame):
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

# Example usage
input_data = pd.DataFrame([{
    'glucose_level_value': 136.8153, 
    'finger_stick_value': 0, 
    'basal_value': 0.2, 
    'basis_gsr_value': 0.1, 
    'basis_skin_temperature_value': 32, 
    'bolus_dose': 0
}], columns=['glucose_level_value', 'finger_stick_value', 'basal_value', 'basis_gsr_value', 'basis_skin_temperature_value', 'bolus_dose'])

# Call predict_single_entry with the example input_data
predicted_value = predict_single_entry(input_data)
print("Predicted BGL value:", predicted_value)