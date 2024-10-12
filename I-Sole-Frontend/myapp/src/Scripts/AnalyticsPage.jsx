import React from 'react';
import { useEffect, useState } from 'react';
import '../Styles/AnalyticsPage.css'; // Make sure to create a corresponding Analytics.css file
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import barchart from '../images/barchart.png';
import linechart from '../images/linechart.png';
import blood from '../images/blood.png'
import sweat from '../images/sweat.png'
import feet from '../images/feet.png'
import piechart from '../images/piechart.png'
import ToggleSwitch from './ToggleSwitch';
import glucoseDayChart from '../images/day.png';
import glucoseWeekChart from '../images/week.png';
import glucoseMonthChart from '../images/month.png';
import footImage from '../images/foot.png'
import { firestore } from '../firebase';
import { doc, collection, onSnapshot } from 'firebase/firestore';

let connectionURL = localStorage.getItem('API_URL'); 
function Analytics() {
  const navigate = useNavigate(); // Hook to access the history instance

  const [currUsername, setCurrUsername] = useState('');
  const [selectedTimeframe, setSelectedTimeframe] = useState('Day');
  const [predictionState, setPredictionState] = useState('');
  const [predictionTime, setPredictionTime] = useState('');
  const [predictionImage, setPredictionImage] = useState('');

  // State to control if the prediction image should be shown
  const [showGlucosePrediction, setshowGlucosePrediction] = useState(false);
  const [showPressurePrediction, setshowPressurePrediction] = useState(false);
  const [basalValue, setBasalValue] = useState('-');
  const [bolusDose, setBolusDose] = useState('-');
  const [basisGsrValue, setBasisGsrValue] = useState('-');
  const [basisSkinTemperatureValue, setBasisSkinTemperatureValue] = useState('-');
  const [fingerStickValue, setFingerStickValue] = useState('-');
  const [sweatGlucose, setSweatGlucose] = useState(null);
  const [bloodGlucose, setBloodGlucose] = useState(null);
  const [footRegion, setFootRegion] = useState('p1');
  const [pressurePlotImage, setPressurePlotImage] = useState('');
  const [riskData, setRiskData] = useState(null);
  const [maxPressure, setMaxPressure] = useState(0);

  // Add state for controlling overlay visibility
  const [isOverlayVisible, setIsOverlayVisible] = useState(false);

  // State for the current plot to display
  const [currentPlot, setCurrentPlot] = useState('');

  const start_data_faker = async (currUsername) => {      
    // Call the start_data_faker endpoint to start faking pressure and glucose data in the backend. 
    console.log(`this is the current username ${currUsername}`);
    axios.post(`${connectionURL}/start_data_faker`, { 'username': currUsername })
        .then(response => {
            console.log('Data faker started:', response.data);
        })
        .catch(error => {
            console.error('Error starting data faker:', error);
        });
  }

  // Effect to set the currUsername from localStorage
  useEffect(() => {
    const username = localStorage.getItem('curr_username');
    setCurrUsername(username);

  }, []); // Runs once after the initial render

  useEffect(()=>{
    if(currUsername){
      start_data_faker(currUsername);
    } 
  },[currUsername]
  )

  // Effect to make API calls when currUsername changes
  useEffect(() => {
    if (currUsername) {
      const fetchData = async () => {
        try {
          console.log("User inside listener: ", currUsername);

          // Ensure that the username is available before making API calls
          await getLatestGlucose();
          await fetchPressureRiskData();
          await fetchPersonalMetrics();

          // Additional calls to generate images and handle pressure data can be made here
        } catch (error) {
          console.error("Error fetching data: ", error);
        }
      };

      fetchData();
    }
  }, [currUsername]); // Runs when currUsername changes
      
  const makePrediction = async () => {
    try {
      const glucoseValues = await getLatestGlucose(); // Use the returned values here
  
      // Check if glucoseValues are undefined (which means getLatestGlucose failed)
      if (!glucoseValues) {
        console.error("Failed to fetch glucose values for prediction.");
        return; // Exit the function if we don't have the required values
      }
  
      console.log("After await latest glucose value: ", glucoseValues.bloodGlucose);
  
      const data = {
        "input_data": {
          "glucose_level_value": glucoseValues.bloodGlucose,
          "finger_stick_value": fingerStickValue,
          "basal_value": basalValue,
          "basis_gsr_value": basisGsrValue, 
          "basis_skin_temperature_value": basisSkinTemperatureValue,
          "bolus_dose": bolusDose
        },
        "hyperglycemia_threshold": 200,
        "hypoglycemia_threshold": 70
      };
  
      console.log("Data sent to plot prediction: ", data);
  
      const response = await axios.post(`${connectionURL}/plot-prediction`, data);
  
      console.log(response);
  
      const { image, prediction_state, prediction_time } = response.data;
  
      console.log("Prediction State:", prediction_state);
      console.log("Prediction Time:", prediction_time);
  
      // Assuming you want to display the image directly without saving it locally
      const imageUrl = `data:image/png;base64,${image}`;
  
      // Update state or do further processing with the image URL
      setPredictionState(prediction_state);
      setPredictionTime(prediction_time);
      setPredictionImage(imageUrl); // This sets the base64 image URL to state
      setshowGlucosePrediction(true); // Set a flag to show the prediction UI
    } catch (error) {
      console.error('Error making the prediction:', error);
      if (error.response) {
        console.error("Error Response:", error.response);
      }
    }
  };
  
  

  // This function fetches the latest glucose data for a given user.
  const getLatestGlucose = async () => {
    try {
        const username = currUsername;
        const response = await axios.get(`${connectionURL}/get_latest_glucose/${username}`);

        if (response.data.success) {
            const { sweatGlucose, bloodGlucose } = response.data.latestGlucoseValue;

            setSweatGlucose(sweatGlucose);
            setBloodGlucose(bloodGlucose);

            return { sweatGlucose, bloodGlucose }; 
        } else {
            console.error('Failed to fetch latest glucose data:', response.data.message);
        }
    } catch (error) {
        console.error('Error fetching latest glucose data:', error);
    }
  };
    
  const resetPrediction = () => {
    // Reset to show the default day chart and hide the prediction image
    setshowGlucosePrediction(false);
    setPredictionImage(glucoseDayChart); // Revert to the default day chart image
    setBasalValue('-');
    setBolusDose('-');
    setBasisGsrValue('-');
    setBasisSkinTemperatureValue('-');
    setFingerStickValue('-');
  };

  //Working correctly 
  const fetchPersonalMetrics = async () => {
    const username = currUsername; // Define the username
    console.log(`username = ${username}`);  
    const params = {
      'username' : username
    }
    const endpoint = `${connectionURL}/get_personal_metrics`; 

    try {
      const response = await axios.get(endpoint , {params});
      
      // Extract and store only the values of the specified fields 
      const { 
        basal_value, 
        bolus_dose,  
        basis_gsr_value,
        basis_skin_temperature_value, 
        finger_stick_value 
      } = response.data.data;

      // Update state variables with the extracted values
      setBasalValue(basal_value);
      setBolusDose(bolus_dose);
      setBasisGsrValue(basis_gsr_value);
      setBasisSkinTemperatureValue(basis_skin_temperature_value);
      setFingerStickValue(finger_stick_value); 
    } catch (error) {
      console.error('Error fetching personal metrics:', error); 
    }
  };


  const closeModal = () => {
    setIsOverlayVisible(false);
    setFootRegion(''); // Reset the foot region to indicate no selection
  };

  // Function to handle region button clicks
  const handleRegionButtonClick = (region) => {
    setFootRegion(region);
    fetchPressurePlotImage(region); // This will handle setting the current plot and showing overlay once fetch completes
    setIsOverlayVisible(true); // Show overlay here to ensure it happens after image is ready
  };

  const fetchPressurePlotImage = (region) => {

    const username = currUsername;
    // console.log('footRegion: ', region)
    // console.log('fetchPressurePlotImage called')

    // Get the current time and the time 30 minutes ago
    const endTimestamp = new Date();
    const startTimestamp = new Date(endTimestamp.getTime() - 30 * 60000); // 30 minutes in milliseconds

    // Function to format the date to ISO string with microseconds
    const formatTimestamp = (date) => {
        const isoString = date.toISOString();
        const [datePart, timePart] = isoString.split('T');
        const [time, milli] = timePart.split('.');
        const microseconds = milli.slice(0, 6); // Get the first 6 digits of the milliseconds
        return `${datePart}T${time}.${microseconds}`;
    };

    const startTimestampEdmonton = formatTimestamp(startTimestamp);
    const endTimestampEdmonton = formatTimestamp(endTimestamp);

    const url = `${connectionURL}/plot_pressure?username=${username}&start_timestamp=${startTimestampEdmonton}&end_timestamp=${endTimestampEdmonton}&region=${region}`;

    // Make the GET request with the constructed URL
    axios.get(url, {
      responseType: 'blob' // Indicates that the response data should be treated as a Blob
    })
    .then(response => {
      // Create a local URL for the blob object
      const imageUrl = URL.createObjectURL(response.data);
      setPressurePlotImage(imageUrl); // Use this URL for displaying the image
      setCurrentPlot(imageUrl); // Now update currentPlot with the new imageUrl
    })
    .catch(error => {
      console.error('There was an error fetching the plot image:', error);
    });
  };


  const fetchPressureRiskData = async () => {
    try {
      // Get the current timestamp
      const endTimestamp = new Date().toISOString();

      // Calculate the timestamp for 30 minutes ago
      const startTimestamp = new Date(Date.now() - 30 * 60 * 1000).toISOString();

      // Make the GET request with the required query parameters
      console.log(currUsername);
      const response = await axios.get(`${connectionURL}/get_average_pressure/${currUsername}`, {
        params: {
          'start': startTimestamp,
          'end': endTimestamp,
          'footRegion': footRegion
        }
      });

      if (response.data.success) {
        console.log("Pressure risk data fetched successfully:", response.data);
        setRiskData(response.data.data);
        setMaxPressure(response.data.averagePressure);
      } else {
        console.error("Failed to fetch pressure risk data:", response.data.message);
      }
    } catch (err) {
      console.error("Error fetching pressure risk data:", err.message);
    }
  };
  


  return (
    <div className="app">
      <main className="analytics-content">
          <div className="top-row">
                <div className="card blood-glucose">
                  <div className="card-header">
                    <img src={blood} alt="Blood Glucose Icon" className="icon" />
                    <p>Blood Glucose Level</p>
                  </div>
                  <h1>{bloodGlucose ? `${bloodGlucose} mg/dL` : '-'}</h1>
                  <span className={bloodGlucose > 165 ? "positive" : "negative"}>
                  {bloodGlucose !== null ? (bloodGlucose > 165 ? '+6%' : '-6%') : ''}
                  </span>

                </div>
                <div className="card retina-pressure"> 
                  <div className="card-header">
                    <img src={feet}  alt="Retina Pressure Icon" className="icon" />
                    <p>Plantar Pressure Level</p>
                  </div>
                  <h1>{maxPressure ? `${maxPressure} kPa` : '-'}</h1>
                </div>
                <div className="card blood-glucose">
                  <div className="card-header">
                    <img src={sweat}  alt="Sweat Glucose Icon" className="icon" />
                    <p>Sweat Glucose Level</p>
                  </div>
                  <h1>{sweatGlucose ? `${sweatGlucose} μmol/L` : '-'}</h1>
                  <span className={sweatGlucose > 100 ? "positive" : "negative"}>
                    {sweatGlucose !== null ? (sweatGlucose > 100 ? '+4%' : '-4%') : ''}
                  </span>
                </div>
          </div>

          <div className="main-content">
            <div className="chart glucose-sensor-analytics">
                <div className="chart-header">
                  <h1>Glucose Sensor Analytics</h1>
                  <ToggleSwitch onToggle={setSelectedTimeframe} />
                </div>
                {selectedTimeframe === 'Day' && (
                  <img src={showGlucosePrediction ? predictionImage : glucoseDayChart} alt="Glucose Sensor Analytics Chart - Day" />
                )}
                {selectedTimeframe === 'Week' && (
                  <img src={glucoseWeekChart} alt="Glucose Sensor Analytics Chart - Week" />
                )}
                {selectedTimeframe === 'Month' && (
                  <img src={glucoseMonthChart} alt="Glucose Sensor Analytics Chart - Month" />
                )}
                <div className="buttons-container">
                  <button className="reset-button" onClick={resetPrediction}>Reset</button> 
                  <button className="make-prediction-button" onClick={makePrediction}>Make Prediction</button>
                </div>
              </div>

            <div className="chart pressure-sensor-analytics">
              <h1>Pressure Sensor Analytics</h1>
              <div className="footBox">
                <div className="footContainer">
                  <img src={footImage} alt="Foot" className="footIcon" /> 
                  <div className="regionContainer">
                    <button
                      className={`regionButton regionButton1 ${footRegion === 'p1' ? 'selectedToggle' : ''}`}
                      onClick={() => handleRegionButtonClick('p1')}>
                      P1
                    </button>
                    <button
                      className={`regionButton regionButton2 ${footRegion === 'p5' ? 'selectedToggle' : ''}`}
                      onClick={() => handleRegionButtonClick('p5')}>
                      P5
                    </button>
                    <button
                      className={`regionButton regionButton3 ${footRegion === 'p6' ? 'selectedToggle' : ''}`}
                      onClick={() => handleRegionButtonClick('p6')}>
                      P6
                    </button>
                    <button
                      className={`regionButton regionButton4 ${footRegion === 'p3' ? 'selectedToggle' : ''}`}
                      onClick={() => handleRegionButtonClick('p3')}>
                      P3
                    </button>
                    <button
                      className={`regionButton regionButton5 ${footRegion === 'p2' ? 'selectedToggle' : ''}`}
                      onClick={() => handleRegionButtonClick('p2')}>
                      P2
                    </button>
                    <button
                      className={`regionButton regionButton6 ${footRegion === 'p4' ? 'selectedToggle' : ''}`}
                      onClick={() => handleRegionButtonClick('p4')}>
                      P4
                    </button>

                  </div>
                </div>
              </div>
              <button className="reset-button" onClick={resetPrediction}>Reset</button> 
            </div>

            <div className='card_prediction_group'>
              <div className="card predictions">
                  <h1>Predictions</h1>
                  <ul className="predictions-list">

                  <li>
                      Diabetic Ulceration
                      <ul>
                      {Object.entries(riskData || {}).map(([key, risk]) => {
                          // Transform "P1_RISK" to "P1"
                          const formattedKey = key.replace("_RISK", "").toUpperCase();

                          // Capitalize the first letter of each word in the risk string
                          const formattedRisk = risk ? risk.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ') : '-';

                          return (
                            <li key={key}>
                              {formattedKey} <strong className={risk ? risk.toLowerCase() + '-risk' : ''}>
                                {formattedRisk + ' Risk' || '-'}
                              </strong>
                            </li>
                          );
                        })}
                    </ul>
                    </li>
                    <li>Hypoglycemia <strong className={
                      showGlucosePrediction && predictionState === 'hypoglycemia' ? 
                      "high-risk" : 
                      (showGlucosePrediction ? 'low-risk' : '')
                    }>
                    {
                      showGlucosePrediction && predictionState === 'hypoglycemia' ? 
                      `High Risk - ${predictionTime}` : 
                      (showGlucosePrediction ? 'Low Risk' : '-')
                    }
                    </strong></li>
                    <li>Hyperglycemia <strong className={
                      showGlucosePrediction && predictionState === 'hyperglycemia' ? 
                      "high-risk" : 
                      (showGlucosePrediction ? 'low-risk' : '')
                    }>
                    {
                      showGlucosePrediction && predictionState === 'hyperglycemia' ? 
                      `High Risk - ${predictionTime}` : 
                      (showGlucosePrediction ? 'Low Risk' : '-')
                    }
                    </strong></li>
                  </ul>
              </div>
                    
              <div className="card predictions">
                <h1>Personal Metrics</h1>
                <ul className="predictions-list">
                  <li>Basal Dosage <strong className={basalValue !== '-' ? "low-risk" : "golden"}>{basalValue !== '-' ? `${basalValue} units` : basalValue}</strong></li>
                  <li>Bolus Dosage <strong className={bolusDose !== '-' ? "low-risk" : "golden"}>{bolusDose !== '-' ? `${bolusDose} units` : bolusDose}</strong></li>
                  <li>Basis GSR <strong className={basisGsrValue !== '-' ? "low-risk" : "golden"}>{basisGsrValue !== '-' ? `${basisGsrValue} mg/dL` : basisGsrValue}</strong></li>
                  <li>Basis Skin Temperature <strong className={basisSkinTemperatureValue !== '-' ? "low-risk" : "golden"}>{basisSkinTemperatureValue !== '-' ? `${basisSkinTemperatureValue} °F` : basisSkinTemperatureValue}</strong></li>
                  <li>Finger Stick Value <strong className={fingerStickValue !== '-' ? "low-risk" : "golden"}>{fingerStickValue !== '-' ? `${fingerStickValue} units` : fingerStickValue}</strong></li>
                </ul>
              </div>
            </div>

          </div>
      </main>


      {isOverlayVisible && (
        <div className="overlay" onClick={closeModal}>
          <div className="overlay-content" onClick={(e) => e.stopPropagation()}>
            <img src={currentPlot} alt="Plot" />
            <button onClick={closeModal}>Close</button>
          </div>
        </div>
      )}


    </div>
  );
}

export default Analytics;
