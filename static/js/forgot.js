const firebaseConfig = {
    apiKey: "AIzaSyAZNQxPhPOMeGgblrlEDt0xbKysz8oOtmk",
    authDomain: "leafcure-9eeab.firebaseapp.com",
    projectId: "leafcure-9eeab",
    storageBucket: "leafcure-9eeab.firebasestorage.app",
    messagingSenderId: "839597084680",
    appId: "1:839597084680:web:2d7e5cba7913d0dba481bd"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

function resetPassword() {
    const email = document.getElementById("email").value;

    auth.sendPasswordResetEmail(email)
        .then(() => {
            document.getElementById("msg").innerHTML =
                "✔ Password reset email sent! Check your inbox.";
        })
        .catch((error) => {
            document.getElementById("msg").innerHTML = error.message;
        });
}