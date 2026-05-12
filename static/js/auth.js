/* ================================
   STATIC USERS (LOCAL / OFFLINE)
================================ */
import {renderApp} from "./addUi.js";

const USERS = [
    {email: "admin@example.com", password: "Admin@123456", role: "admin"},
    {email: "operator@example.com", password: "Operator@123456", role: "operator"},
    {email: "manager@example.com", password: "Manager@123456", role: "manager"}
];

/* ================================
   LOGIN HANDLER (ATTACH AFTER UI)
================================ */
export function attachLoginHandler() {
    const form = document.getElementById("loginForm");
    if (!form) {
        console.warn("loginForm not found");
        return;
    }

    form.addEventListener("submit", handleLogin);
}

function handleLogin(e) {
    e.preventDefault(); // 🔴 STOP PAGE RELOAD

    clearErrors();

    const emailEl = document.getElementById("email");
    const passwordEl = document.getElementById("password");

    let isValid = true;

    /* -------- EMAIL VALIDATION -------- */
    if (!emailEl.value.trim()) {
        showError(emailEl, "Email is required");
        isValid = false;
    } else if (!isValidEmail(emailEl.value.trim())) {
        showError(emailEl, "Invalid email format");
        isValid = false;
    }

    /* -------- PASSWORD VALIDATION -------- */
    const pwdError = validatePassword(passwordEl.value.trim());
    if (pwdError) {
        showError(passwordEl, pwdError);
        isValid = false;
    }

    if (!isValid) {
        console.log("❌ Validation failed");
        return; // 🔴 STOP EXECUTION
    }

    /* -------- AUTH CHECK -------- */
    const user = USERS.find(
        u =>
            u.email === emailEl.value.trim() &&
            u.password === passwordEl.value.trim()
    );

    if (!user) {
        showError(passwordEl, "Invalid email or password");
        return;
    }

    /* -------- SAVE AUTH -------- */
    localStorage.setItem(
        "auth",
        JSON.stringify({
            isAuth: true,
            role: user.role,
            email: user.email
        })
    );

    alert(`✅ Logged in as ${user.role.toUpperCase()}`);
    renderApp()
    //  setTimeout(() => {
    //     window.location.reload();
    // }, 1000)
}

/* ================================
   ROUTE GUARD
================================ */
export function protectPage() {
    const auth = JSON.parse(localStorage.getItem("auth"));
    if (!auth?.isAuth) {
        alert("Please login first");
        // window.location.href = "login.html";
    }
}

/* ================================
   ROLE-BASED ACCESS
================================ */


export function applyRoleAccess() {
    const ROLE_UI_RULES = {
        admin: {
            disable: []
        },

        manager: {
            disable: ["panel-config",
                "panel-simulator",
                "panel-dashboard",
                "panel-hybrid",
                "panel-softsensor",
                "panel-mbrl",
                "panel-softsensor-sim",
                "panel-trends"]
        },

        operator: {
            disable: [
                "panel-config",
            ]
        }
    };

    const auth = JSON.parse(localStorage.getItem("auth"));
    if (!auth) return;

    const roleText = document.getElementById("roleText");
    const roleTextP = document.getElementById("roleText");

    if (roleText && roleTextP) {
        roleText.textContent = `${auth.role.toUpperCase()}`;
        roleTextP.textContent = `${auth.role.toUpperCase()}`;

    }

    const rules = ROLE_UI_RULES[auth.role];
    if (!rules) return;

    rules.disable.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;

        el.classList.add("ui-disabled");
        el.setAttribute("aria-disabled", "true");
        el.setAttribute(
            "data-tooltip",
            `${auth.role.toUpperCase()} – restricted`
        );

        // form elements
        if ("disabled" in el) {
            el.disabled = true;
        }
    });
}

/* ================================
   LOGOUT
================================ */
export function logout() {
    localStorage.removeItem("auth");
    alert("Logged out");
    // renderApp()
    setTimeout(() => {
        window.location.reload();
    }, 1000)
}

/* ================================
   VALIDATION HELPERS
================================ */
export function validatePassword(value) {
    if (!value) return "Password is required";
    if (value.length < 12) return "Minimum 12 characters";
    if (!/[A-Z]/.test(value)) return "At least 1 uppercase letter";
    if (!/[a-z]/.test(value)) return "At least 1 lowercase letter";
    if (!/[0-9]/.test(value)) return "At least 1 number";
    if (!/[@$!%*?&]/.test(value))
        return "At least 1 special character";
    return null; // ✅ VALID
}

export function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/* ================================
   ERROR HELPERS
================================ */
export function showError(input, message) {
    const errorEl = input.parentElement.querySelector(".error");
    if (errorEl) errorEl.textContent = message;
}

export function clearErrors() {
    document.querySelectorAll(".error").forEach(e => (e.textContent = ""));
}