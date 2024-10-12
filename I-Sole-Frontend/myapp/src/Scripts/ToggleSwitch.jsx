import React, { useState } from 'react';
import '../Styles/ToggleSwitch.css'; // Path to your CSS file

function ToggleSwitch({ onToggle }) {
  const [selectedOption, setSelectedOption] = useState('Day');

  return (
    <div className="toggle-switch">
      <button
        className={`toggle-option ${selectedOption === 'Day' ? 'selected' : ''}`}
        onClick={() => {
          setSelectedOption('Day');
          onToggle('Day'); // Add this line
        }}
      >
        Day
      </button>
      <button
        className={`toggle-option ${selectedOption === 'Week' ? 'selected' : ''}`}
        onClick={() => {
          setSelectedOption('Week');
          onToggle('Week'); // Add this line
        }}
      >
        Week
      </button>
      <button
        className={`toggle-option ${selectedOption === 'Month' ? 'selected' : ''}`}
        onClick={() => {
          setSelectedOption('Month');
          onToggle('Month'); // Add this line
        }}
      >
        Month
      </button>
    </div>
  );
}

export default ToggleSwitch;
