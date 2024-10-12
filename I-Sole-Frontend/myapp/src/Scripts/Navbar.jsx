import React from 'react';
import { useEffect, useState } from 'react';
import logo from '../images/logo.png';
import { useNavigate } from 'react-router-dom';
import profileImage from '../images/dummy_profile_image.png'
import '../Styles/Navbar.css'; // Ensure this imports your CSS file

const Navbar = () => {
    const [currUsername, setCurrUsername] = useState('');
    const navigate = useNavigate(); // Hook to access the history instance

    useEffect(
        ()=>{
            setCurrUsername(localStorage.getItem('curr_username'))
        },[]
    );

    const handleSignOut = () => {
        localStorage.clear();
        navigate('/login') ; 
    };

    return (
        <nav className="navbar">
            <img src={logo} alt="I-Sole Diabetic Tracking" />
            <h1>User Analytics</h1>

            <div className="navbar-profile">

                <img src={profileImage} alt={currUsername} />
                <div className='navbar-profile-inner'>
                    <div className="navbar-profile-name">
                    {currUsername}
                    </div>
                    <button className="signout-button" onClick={handleSignOut}>
                    ➜
                    </button>
                </div>
                
            </div>
            
        </nav>
    );
};

export default Navbar;
