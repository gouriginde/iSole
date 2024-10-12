import React from 'react';
import '../Styles/LoginPage.css'; // Make sure this is the correct path to your CSS file
import logo from '../images/logo.png';
import sugar_machine from '../images/homepage-image.png';
import { useNavigate  } from 'react-router-dom';
import '../Styles/Homepage.css'

const HomePageNavbar = () => {
    const navigate = useNavigate(); 

    const handleLogin = () => {
        localStorage.clear();
        navigate('/login') ; 
    };

    return(
        <div className='homepage-navbar'>
            <img src={logo} alt="I-Sole Diabetic Tracking" />
            <button onClick={handleLogin}>Login</button>
        </div>
    )
}

const HomePage = () => {

    return(
        <div className='homepage'>
            <HomePageNavbar />
            <div className='homepage-section section1'>
                <h1 className='main--heading'>Transforming Health Monitoring</h1>
            </div>
            <div className='homepage-section section2 no-overlay'>
                <img src={sugar_machine} alt="Usual Diabetic Tracker" className='homepage-showcase-image' />
                <div className='homepage-textblock'>
                    <h1 className='secondary--heading--dark'>Facts that prompt a change</h1>
                    <ul className='homepage-textblock'>
                        <li>Invasive blood glucose monitoring methods.</li>
                        <li>Lack of continuous glucose monitoring systems.</li>
                        <li>No predictive analysis for potential glucose level spikes or drops.</li>
                        <li>Inadequate real-time alerts for abnormal glucose levels.</li>
                    </ul>

                </div>
            </div>
            <div className='homepage-section section3'>
                <div class="responsive-iframe-container">
                    <iframe src="https://www.youtube.com/embed/9RFtb5bIhGk?si=YT06F5G0bm6ooyr9" 
                            title="YouTube video player" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                            referrerpolicy="strict-origin-when-cross-origin" 
                            allowfullscreen>
                    </iframe>
                </div>
            </div>
        </div>
    )
 
};

export default HomePage;
