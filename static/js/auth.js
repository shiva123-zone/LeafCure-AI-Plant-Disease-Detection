const firebaseConfig = {
    apiKey: "AIzaSyAZNQxPhPOMeGgblrlEDt0xbKysz8oOtmk",
    authDomain: "leafcure-9eeab.firebaseapp.com",
    projectId: "leafcure-9eeab",
    storageBucket: "leafcure-9eeab.firebasestorage.app",
    messagingSenderId: "839597084680",
    appId: "1:839597084680:web:2d7e5cba7913d0dba481bd"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// Email Password Login
async function emailLogin() {
    let email = document.getElementById("email").value;
    let pass  = document.getElementById("password").value;

    try {
        let res = await auth.signInWithEmailAndPassword(email, pass);
        let idToken = await res.user.getIdToken();

        // send to backend to store user data
        sendUserToBackend(res.user, idToken);

        window.location.href = "/dashboard";
    } catch (e) {
        document.getElementById("msg").innerText = e.message;
    }
}

// Google Login
async function googleLogin() {
    let provider = new firebase.auth.GoogleAuthProvider();
    try {
        let res = await auth.signInWithPopup(provider);
        let idToken = await res.user.getIdToken();

        // send to backend to store user data
        sendUserToBackend(res.user, idToken);

        window.location.href = "/dashboard";
    } catch (e) {
        document.getElementById("msg").innerText = e.message;
    }
}

// Send to backend
async function sendUserToBackend(user, idToken) {
    await fetch("/api/store_user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": idToken
        },
        body: JSON.stringify({
            uid: user.uid,
            name: user.displayName || "",
            email: user.email
        })
    });
}