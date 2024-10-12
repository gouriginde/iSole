import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../Styles/SignupPage.css'; // Make sure this is the correct path to your CSS file
import logoImage from '../images/logo.png'; // Update with the correct path to your logo image
import google from '../images/google.png'; // Update with the correct path to your logo image
import outlook from '../images/outlook.png'; // Update with the correct path to your logo image
import { useNavigate  } from 'react-router-dom';

const SignupPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState(''); // State for username
  const navigate = useNavigate();  // Hook to access the history instance
  const [connectionURL, setConnectionURL] = useState(localStorage.getItem('API_URL') || '');

  useEffect(
    () => {
      console.log(`api url from signup page -> ${connectionURL}`);
    }, []
  );

  const handleSignUp = async (e) => {
    e.preventDefault();

    try {
        const signupResponse = await axios.post(`${connectionURL}/signup`, {
            username: username,
            email: email,
            password: password,
            fullName: fullName,
        });

        if (signupResponse.data.success) {
            console.log("Account created successfully");

            // Store the username in local storage
            localStorage.setItem('curr_username', username);

            navigate('/analytics');  // Redirect to '/feedback' route
        } else {
            console.log("Failed to create account");
        }
      } catch (error) {
          console.error('Error during sign up:', error);
      }
  };

  return (
    <div className="signup-page-container">
      <div className="signup-image-section">
        {/* This will be the left side with your image or design */}
        <img src={logoImage} alt="I-Sole Diabetic Tracking" />
      </div>
      <div className="signup-form-container">
        <div className="signup-form">
          <h1>Create Account</h1>
          <form onSubmit={handleSignUp}>
            <input
              type="text"
              placeholder="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            <input
              type="text"
              placeholder="Username" // New input field for username
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <input
              type="email"
              placeholder="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button type="submit" className="create-account-button">Create Account</button>
          </form>
          <div className="signup-footer">
            <p>
              <a href="#/login">Already have an account?</a>
            </p>
          </div>

        </div>
      </div>
    </div>
  );
};

export default SignupPage;
