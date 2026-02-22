const firebaseConfig = {
  apiKey: "AIzaSyAZNQxPhPOMeGgblrlEDt0xbKysz8oOtmk",
  authDomain: "leafcure-9eeab.firebaseapp.com",
  projectId: "leafcure-9eeab",
  appId: "1:839597084680:web:2d7e5cba7913d0dba481bd"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

async function registerUser() {
    // Get all form values
    let name = document.getElementById("name").value;
    let age = document.getElementById("age").value;
    let contact = document.getElementById("contact").value;
    let address = document.getElementById("address").value;
    let email = document.getElementById("email").value;
    let pass = document.getElementById("password").value;
    
    // Basic validation
    if (!name || !email || !pass) {
        document.getElementById("msg").innerText = "❌ Please fill required fields!";
        return;
    }

    try {
        // Create Firebase account
        let res = await auth.createUserWithEmailAndPassword(email, pass);
        
        // Update user's display name in Firebase
        await res.user.updateProfile({
            displayName: name
        });
        
        // Get ID token
        let idToken = await res.user.getIdToken();

        // Send complete user data to backend
        await fetch("/api/store_user", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": idToken
            },
            body: JSON.stringify({
                uid: res.user.uid,
                name: name,
                age: age || "",
                contact: contact || "",
                address: address || "",
                email: res.user.email
            })
        });

        // Success message
        document.getElementById("msg").innerText = "✅ Account created! Redirecting...";
        document.getElementById("msg").style.color = "#4CAF50";
        
        // Redirect to dashboard after 1.5 seconds
        setTimeout(() => {
            window.location.href = "/dashboard";
        }, 1500);

    } catch (err) {
        // Show error message
        document.getElementById("msg").innerText = "❌ " + err.message;
        document.getElementById("msg").style.color = "#ff6b6b";
    }
}