import React, { useState, useEffect } from 'react';
import '../Styles/LoginPage.css'; // Make sure this is the correct path to your CSS file
import logoImage from '../images/logo.png'; // Update with the correct path to your logo image
import google from '../images/google.png'; // Update with the correct path to your logo image
import outlook from '../images/outlook.png'; // Update with the correct path to your logo image
import axios from 'axios'; // Import axios for making API requests
import { useNavigate  } from 'react-router-dom';


// let connectionURL = localStorage.getItem('API_URL');
const LoginPage = () => {
  const [username, setUsername] = useState(''); // Change to username
  const [password, setPassword] = useState('');
  const navigate = useNavigate();  // Hook to access the history instance
  const [connectionURL, setConnectionURL] = useState(localStorage.getItem('API_URL') || '');

  const handleSignIn = async (e) => { // Change the function name to handleSignIn
    e.preventDefault();
    console.log(connectionURL);

    try {
      // Make a POST request to your backend sign-in endpoint
      const response = await axios.post(`${connectionURL}/signin`, {
        username: username, // Use the username state variable
        password: password,
      });

      if (response.data.success) {
        // Authentication successful
        const { username, patientID, role } = response.data.user_data;
      
        // Store curr_username and patientID in local storage
        localStorage.setItem('curr_username', username);
      
        // Log curr_username for debugging
        console.log('curr_username:', username);
      
        // Redirect to your main application page or dashboard
        navigate('/analytics');  // Redirect to '/analytics' route
      } else {
        // Authentication failed, handle the error (e.g., show an error message)
        console.error('Sign-in failed:', response.data.message);
      }
      
    } catch (error) {
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error(error.response.data);
        console.error(error.response.status);
        console.error(error.response.headers);
      } else if (error.request) {
        // The request was made but no response was received
        console.error(error.request);
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error', error.message);
      }
      console.error(error.config);
    }
    
  };

  return (
    <div className="signup-page-container">
      <div className="signup-form-container">
        <div className="signup-form">
          <h1>Sign In</h1>
          <form onSubmit={handleSignIn}>
            <input
              type="text" 
              placeholder="Username" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button type="submit" className="create-account-button">Sign In</button>
          </form>
          <div className="signup-footer">
            <p>
              <a href="#signup">Don't have an account?</a>
            </p>
          </div>

        </div>
      </div>

      <div className="signup-image-section">
        {/* This will be the left side with your image or design */}
        <img src={logoImage} alt="I-Sole Diabetic Tracking" />
      </div>

    </div>
  );
};

export default LoginPage;
