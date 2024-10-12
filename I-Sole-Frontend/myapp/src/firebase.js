// Import the functions you need from the SDKs you need
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyC6sMzy1QQvaorLStq67a7ApL7zZTSd27w",
    authDomain: "i-sole-new.firebaseapp.com",
    projectId: "i-sole-new",
    storageBucket: "i-sole-new.appspot.com",
    messagingSenderId: "458816858957",
    appId: "1:458816858957:web:046428876f5ebc0e2fa504",
    measurementId: "G-226B2B9EX4"
  };

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
const firestore = getFirestore(app);

export { firestore };