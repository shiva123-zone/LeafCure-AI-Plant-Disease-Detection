// Load Saved Theme
window.onload = function () {
    let theme = localStorage.getItem("theme");

    if (theme === "dark") {
        document.body.classList.add("dark-mode");
        document.getElementById("themeToggle").checked = true;
    }
};

// Toggle Theme
function switchTheme() {

    if (document.body.classList.contains("dark-mode")) {
        document.body.classList.remove("dark-mode");
        localStorage.setItem("theme", "light");
    } 
    else {
        document.body.classList.add("dark-mode");
        localStorage.setItem("theme", "dark");
    }
}
