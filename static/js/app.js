// Gujarat Smart Recipe Recommendation System - JavaScript

// Firebase Setup for Auth'

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';

import { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged, sendPasswordResetEmail } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';

// Your web app's Firebase configuration

const firebaseConfig = {
  apiKey: "AIzaSyAzXTvL_8AluvsJjCv9Wn98mgLXtkj2I50",
  authDomain: "recipegenie-07.firebaseapp.com",
  databaseURL: "https://recipegenie-07-default-rtdb.firebaseio.com",
  projectId: "recipegenie-07",
  storageBucket: "recipegenie-07.firebasestorage.app",
  messagingSenderId: "977449491053",
  appId: "1:977449491053:web:11e2d54aa81a219a59bd64",
  measurementId: "G-GV6JZFH230"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
// const analytics = getAnalytics(app);
const auth = getAuth(app);
document.body.classList.add('auth-pending');

const DEFAULT_RECIPE_IMAGE = 'https://recipesimages.edgeone.app/default.jpg';

function getRecipeImageUrl(recipe) {
  const imageUrl = String(recipe?.image_url || recipe?.image || '').trim();
  if (/^(https?:\/\/|\/static\/|\/uploads\/)/i.test(imageUrl)) {
    return imageUrl;
  }
  return DEFAULT_RECIPE_IMAGE;
}

function getCurrentUserId() {
  return auth.currentUser?.uid || localStorage.getItem('uid') || '';
}

function closeLoginRequiredDialog() {
  document.querySelector('.auth-required-overlay')?.remove();
}

function openLoginRequiredDialog(options = {}) {
  closeLoginRequiredDialog();

  const {
    title = 'Login required',
    message = 'Please login to continue with this RecipeGenie feature.',
    primaryLabel = 'Login',
    primaryHref = '/login',
    secondaryLabel = 'Create account',
    secondaryHref = '/register'
  } = options;

  const overlay = document.createElement('div');
  overlay.className = 'auth-required-overlay';
  overlay.innerHTML = `
    <div class="auth-required-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-required-title">
      <button type="button" class="auth-required-close" aria-label="Close login dialog">
        <i class="fas fa-times"></i>
      </button>
      <span class="auth-required-kicker">RecipeGenie account</span>
      <h3 id="auth-required-title">${title}</h3>
      <p>${message}</p>
      <div class="auth-required-actions">
        <a href="${primaryHref}" class="btn primary">${primaryLabel}</a>
        <a href="${secondaryHref}" class="btn auth-secondary-btn">${secondaryLabel}</a>
      </div>
    </div>
  `;

  const removeDialog = () => {
    document.removeEventListener('keydown', handleEscape);
    overlay.remove();
  };

  const handleEscape = event => {
    if (event.key === 'Escape') {
      removeDialog();
    }
  };

  overlay.addEventListener('click', event => {
    if (event.target === overlay) {
      removeDialog();
    }
  });

  overlay.querySelector('.auth-required-close')?.addEventListener('click', removeDialog);
  document.addEventListener('keydown', handleEscape);
  document.body.appendChild(overlay);
  overlay.querySelector('.auth-required-actions a')?.focus();
}

function requireLoggedIn(options = {}) {
  const uid = getCurrentUserId();
  if (uid) return uid;
  openLoginRequiredDialog(options);
  return null;
}

function buildInlineLoginPrompt(title, message) {
  return `
    <div class="login-required-inline">
      <span class="login-required-kicker">Login needed</span>
      <h3>${title}</h3>
      <p>${message}</p>
      <div class="login-required-actions">
        <a href="/login" class="btn primary">Login</a>
        <a href="/register" class="btn auth-secondary-btn">Create account</a>
      </div>
    </div>
  `;
}

function setAuthMessage(errorEl, successEl, errorMessage = '', successMessage = '') {
  if (errorEl) {
    errorEl.textContent = errorMessage;
  }
  if (successEl) {
    successEl.textContent = successMessage;
  }
}


// Password validation function (manual, since Firebase doesn't have client-side validatePassword)
function validatePasswordStrength(password) {
  const containsLowercase = /[a-z]/.test(password);
  const containsUppercase = /[A-Z]/.test(password);
  const containsNumber = /\d/.test(password);
  const containsSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  const isLongEnough = password.length >= 6;

  return {
    isValid: containsLowercase && containsUppercase && containsNumber && containsSpecial && isLongEnough,
    errors: [
      !containsLowercase ? 'Must contain at least one lowercase letter' : '',
      !containsUppercase ? 'Must contain at least one uppercase letter' : '',
      !containsNumber ? 'Must contain at least one number' : '',
      !containsSpecial ? 'Must contain at least one special character' : '',
      !isLongEnough ? 'Must be at least 6 characters long' : ''
    ].filter(Boolean)
  };
}

// Register Form (for register.html)
const registerForm = document.querySelector('#register-form');
if (registerForm) {
  const nameInput = document.querySelector('#reg-name');
  const emailInput = document.querySelector('#reg-email');
  const passwordInput = document.querySelector('#password');
  const confirmInput = document.querySelector('#confirm-password');
  const codeInput = document.querySelector('#register-verification-code');
  const sendCodeBtn = document.querySelector('#send-register-code');
  const verifyBtn = document.querySelector('#verify-register-code');
  const codeShell = document.querySelector('#register-code-shell');
  const errorEl = document.querySelector('#reg-error') || document.querySelector('.error');
  const successEl = document.querySelector('#reg-success');
  const codeHelp = document.querySelector('#register-code-help');

  const collectRegistrationData = () => ({
    name: nameInput?.value?.trim() || '',
    email: emailInput?.value?.trim() || '',
    password: passwordInput?.value || '',
    confirm: confirmInput?.value || ''
  });

  const validateRegistrationData = () => {
    const { name, email, password, confirm } = collectRegistrationData();
    if (!name || !email || !password || !confirm) {
      return 'Please complete all registration fields.';
    }
    if (password !== confirm) {
      return 'Passwords do not match!';
    }

    const validation = validatePasswordStrength(password);
    if (!validation.isValid) {
      return validation.errors.join(' ');
    }
    return '';
  };

  sendCodeBtn?.addEventListener('click', async () => {
    const validationMessage = validateRegistrationData();
    if (validationMessage) {
      setAuthMessage(errorEl, successEl, validationMessage, '');
      return;
    }

    const { name, email, password } = collectRegistrationData();
    sendCodeBtn.disabled = true;
    setAuthMessage(errorEl, successEl, '', 'Sending verification code...');

    try {
      const res = await fetch('/auth/send-registration-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || `Server error ${res.status}`);
      }

      if (codeShell) {
        codeShell.style.display = 'grid';
      }
      if (verifyBtn) {
        verifyBtn.disabled = false;
      }
      if (codeHelp) {
        codeHelp.textContent = `We sent a 6-digit verification code to ${email}. Enter it here to finish registration.`;
      }
      setAuthMessage(errorEl, successEl, '', data.message || 'Verification code sent successfully.');
      codeInput?.focus();
    } catch (error) {
      setAuthMessage(errorEl, successEl, error.message || 'Unable to send verification code.', '');
    } finally {
      sendCodeBtn.disabled = false;
    }
  });

  registerForm.addEventListener('submit', async e => {
    e.preventDefault();
    const validationMessage = validateRegistrationData();
    if (validationMessage) {
      setAuthMessage(errorEl, successEl, validationMessage, '');
      return;
    }

    const code = codeInput?.value?.trim() || '';
    if (!code || code.length !== 6) {
      setAuthMessage(errorEl, successEl, 'Enter the 6-digit verification code from your email.', '');
      return;
    }

    const { email, password } = collectRegistrationData();
    verifyBtn.disabled = true;
    setAuthMessage(errorEl, successEl, '', 'Verifying code and creating your account...');

    try {
      const verifyRes = await fetch('/auth/verify-registration-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code })
      });
      const verifyData = await verifyRes.json();

      if (!verifyRes.ok) {
        throw new Error(verifyData.error || `Server error ${verifyRes.status}`);
      }

      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      localStorage.setItem('uid', userCredential.user.uid);
      setAuthMessage(errorEl, successEl, '', 'Account verified successfully. Redirecting...');
      window.location.href = '/home';
    } catch (error) {
      setAuthMessage(errorEl, successEl, error.message || 'Unable to verify registration code.', '');
    } finally {
      verifyBtn.disabled = false;
    }
  });
}

// Login Form (for login.html)
const loginForm = document.querySelector('#login-form');
if (loginForm) {
  const forgotPasswordBtn = document.querySelector('#forgot-password-btn');
  const resendVerificationBtn = document.querySelector('#resend-verification-btn');
  const emailInput = document.querySelector('#login-email') || loginForm.querySelector('input[type="email"]');
  const passwordInput = document.querySelector('#login-password') || loginForm.querySelector('input[type="password"]');
  const errorEl = document.querySelector('#login-error') || document.querySelector('.error');
  const successEl = document.querySelector('#login-success');
  const statusPanel = document.querySelector('#login-status-panel');
  const statusKicker = document.querySelector('#login-status-kicker');
  const statusTitle = document.querySelector('#login-status-title');
  const statusMessage = document.querySelector('#login-status-message');
  let loginStatusRequestToken = 0;

  const updateLoginStatusPanel = ({ mode = 'neutral', kicker = 'Account status', title = 'Waiting for email', message = '' } = {}) => {
    if (!statusPanel || !statusKicker || !statusTitle || !statusMessage) return;
    statusPanel.style.display = 'grid';
    statusPanel.classList.remove('auth-status-neutral', 'auth-status-verified', 'auth-status-unverified', 'auth-status-missing');
    statusPanel.classList.add(`auth-status-${mode}`);
    statusKicker.textContent = kicker;
    statusTitle.textContent = title;
    statusMessage.textContent = message;
  };

  const hideResendButton = () => {
    if (resendVerificationBtn) {
      resendVerificationBtn.style.display = 'none';
    }
  };

  const checkLoginEmailStatus = async () => {
    const email = emailInput?.value?.trim() || '';
    if (!email) {
      if (statusPanel) {
        statusPanel.style.display = 'none';
      }
      hideResendButton();
      return;
    }

    const requestToken = ++loginStatusRequestToken;
    updateLoginStatusPanel({
      mode: 'neutral',
      kicker: 'Checking status',
      title: 'Looking up your account',
      message: 'RecipeGenie is checking whether this email is already verified.'
    });
    hideResendButton();

    try {
      const res = await fetch('/auth/email-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (requestToken !== loginStatusRequestToken) return;

      if (!res.ok) {
        throw new Error(data.error || `Server error ${res.status}`);
      }

      if (!data.exists) {
        updateLoginStatusPanel({
          mode: 'missing',
          kicker: 'Account not found',
          title: 'No RecipeGenie account yet',
          message: data.message || 'Create an account to continue.'
        });
        return;
      }

      if (data.registration_verified) {
        updateLoginStatusPanel({
          mode: 'verified',
          kicker: 'Verified account',
          title: 'This email is ready to log in',
          message: data.message || 'Enter your password to continue.'
        });
        return;
      }

      updateLoginStatusPanel({
        mode: 'unverified',
        kicker: 'Verification pending',
        title: 'Finish email verification first',
        message: data.message || 'Use the resend button below if you need a fresh 6-digit code.'
      });
      if (resendVerificationBtn) {
        resendVerificationBtn.style.display = 'inline-flex';
      }
    } catch (error) {
      if (requestToken !== loginStatusRequestToken) return;
      updateLoginStatusPanel({
        mode: 'missing',
        kicker: 'Status unavailable',
        title: 'Unable to check this account',
        message: error.message || 'Please try again in a moment.'
      });
    }
  };

  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const email = emailInput?.value?.trim() || '';
    const password = passwordInput?.value || '';

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      const statusRes = await fetch(`/auth/account-status/${user.uid}`);
      const statusData = await statusRes.json();

      if (!statusRes.ok) {
        throw new Error(statusData.error || `Server error ${statusRes.status}`);
      }

      if (!statusData.registration_verified) {
        await signOut(auth);
        localStorage.removeItem('uid');
        updateLoginStatusPanel({
          mode: 'unverified',
          kicker: 'Verification pending',
          title: 'This account still needs verification',
          message: 'Use the resend verification button below if you need a new 6-digit code.'
        });
        if (resendVerificationBtn) {
          resendVerificationBtn.style.display = 'inline-flex';
        }
        setAuthMessage(
          errorEl,
          successEl,
          'Your account is not verified yet. Please complete the 6-digit email verification on the register page.',
          ''
        );
        return;
      }

      localStorage.setItem("uid", user.uid);
      setAuthMessage(errorEl, successEl, '', 'Login successful. Redirecting...');
      window.location.href = '/home';
    } catch (error) {
      setAuthMessage(errorEl, successEl, error.message || 'Unable to login.', '');
    }
  });

  emailInput?.addEventListener('blur', checkLoginEmailStatus);
  emailInput?.addEventListener('change', checkLoginEmailStatus);

  resendVerificationBtn?.addEventListener('click', async () => {
    const email = emailInput?.value?.trim() || '';
    if (!email) {
      setAuthMessage(errorEl, successEl, 'Enter your email first so we know where to resend the verification code.', '');
      return;
    }

    resendVerificationBtn.disabled = true;
    setAuthMessage(errorEl, successEl, '', 'Sending a new verification code...');

    try {
      const res = await fetch('/auth/resend-registration-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || `Server error ${res.status}`);
      }

      updateLoginStatusPanel({
        mode: 'unverified',
        kicker: 'Verification code sent',
        title: 'Check your email inbox',
        message: data.message || `A fresh 6-digit code was sent to ${email}.`
      });
      setAuthMessage(errorEl, successEl, '', data.message || `A fresh 6-digit code was sent to ${email}.`);
    } catch (error) {
      setAuthMessage(errorEl, successEl, error.message || 'Unable to resend verification code.', '');
    } finally {
      resendVerificationBtn.disabled = false;
    }
  });

  forgotPasswordBtn?.addEventListener('click', async () => {
    const email = emailInput?.value?.trim() || '';
    if (!email) {
      setAuthMessage(errorEl, successEl, 'Enter your email first to receive a password reset link.', '');
      return;
    }

    forgotPasswordBtn.disabled = true;
    setAuthMessage(errorEl, successEl, '', 'Sending password reset link...');

    try {
      await sendPasswordResetEmail(auth, email);
      setAuthMessage(errorEl, successEl, '', `Password reset link sent to ${email}. Check your inbox.`);
    } catch (error) {
      setAuthMessage(errorEl, successEl, error.message || 'Unable to send password reset link.', '');
    } finally {
      forgotPasswordBtn.disabled = false;
    }
  });
}

// Auth state listener (updates navbar, etc.)
onAuthStateChanged(auth, (user) => {
  const body = document.body;
  const loginLinks = document.querySelectorAll('.login-link');
  const registerLinks = document.querySelectorAll('.register-link');
  const logoutLink = document.querySelector('.logout-link');

  body.classList.remove('auth-pending', 'auth-logged-in', 'auth-logged-out');
  body.classList.add('auth-ready');

  if (user) {
    body.classList.add('auth-logged-in');
    // User logged in - hide login/register, show logout
    loginLinks.forEach(link => link.style.display = 'none');
    registerLinks.forEach(link => link.style.display = 'none');
    if (logoutLink) logoutLink.style.display = '';
    localStorage.setItem('uid', user.uid);  // For backend use
    closeLoginRequiredDialog();
  } else {
    body.classList.add('auth-logged-out');
    // User logged out - show login/register
    loginLinks.forEach(link => link.style.display = '');
    registerLinks.forEach(link => link.style.display = '');
    if (logoutLink) logoutLink.style.display = 'none';
    localStorage.removeItem('uid');
  }
});


// Logout
const logoutBtn = document.getElementById('logout');
if (logoutBtn) {
  logoutBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    try {
      await signOut(auth);
      location.reload();
    } catch (error) {
      console.error('Logout error:', error);
    }
  });
}


// Mobile menu toggle
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
if (hamburger) {
  hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('active');
  });
}

document.querySelectorAll('.nav-menu a').forEach(link => {
  const linkPath = new URL(link.href, window.location.origin).pathname;
  if (linkPath === window.location.pathname) {
    link.classList.add('active');
  }
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/service-worker.js');
  }

// Ingredient tags
const ingredientInput = document.getElementById('ingredient');
const tagsContainer = document.getElementById('tags-container');
const ingredientCounter = document.getElementById('ingredient-counter');
const selectedIngredientsPreview = document.getElementById('selected-ingredients-preview');
const addBtn = document.getElementById('add-ingredient');
const findBtn = document.getElementById('find-recipes');
const imageDetectBtn = document.getElementById('detect-image-ingredients');
const loadingChip = document.getElementById('ingredient-search-loading');

function normalizeIngredient(value = '') {
  return String(value)
    .toLowerCase()
    .trim()
    .replace(/[^\w\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function formatIngredient(value = '') {
  return normalizeIngredient(value)
    .split(' ')
    .filter(Boolean)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function parseIngredientItems(text = '') {
  const cleaned = String(text)
    .toLowerCase()
    .replace(/\b(can you add|please add|i have|i want to add|i want|i need|ingredient|ingredients)\b/g, ' ')
    .replace(/\b(and then|then|also|plus|with|and|as well as)\b/g, ',')
    .replace(/[.!?]/g, ',')
    .replace(/\s+/g, ' ')
    .trim();

  if (!cleaned) return [];

  const parts = cleaned
    .split(/[,;\n]+/)
    .map(item => normalizeIngredient(item))
    .filter(Boolean);

  if (parts.length !== 1) return parts;

  const tokens = parts[0].split(/\s+/).filter(Boolean);
  if (tokens.length <= 1) return parts;

  const fillerWords = new Set(['a', 'an', 'the', 'some', 'few', 'more', 'item']);
  const descriptorWords = new Set([
    'red', 'green', 'black', 'white', 'yellow', 'fresh', 'dry', 'dried', 'sweet',
    'olive', 'coconut', 'mustard', 'curry', 'spring', 'baby', 'ginger', 'garlic'
  ]);
  const suffixWords = new Set([
    'oil', 'powder', 'seed', 'seeds', 'leaf', 'leaves', 'paste', 'sauce', 'flour',
    'juice', 'milk', 'cream', 'beans', 'bean', 'pepper', 'peppers', 'masala',
    'rice', 'dal', 'lentils', 'nuts', 'nut', 'cheese', 'chilli', 'chilies',
    'chillies', 'chili'
  ]);

  const grouped = [];
  for (let index = 0; index < tokens.length;) {
    const current = tokens[index];
    const next = tokens[index + 1];
    const third = tokens[index + 2];

    if (fillerWords.has(current)) {
      index += 1;
      continue;
    }

    if (third && suffixWords.has(third) && (descriptorWords.has(current) || descriptorWords.has(next) || suffixWords.has(next))) {
      grouped.push(normalizeIngredient(`${current} ${next} ${third}`));
      index += 3;
      continue;
    }

    if (next && (suffixWords.has(next) || descriptorWords.has(current))) {
      grouped.push(normalizeIngredient(`${current} ${next}`));
      index += 2;
      continue;
    }

    grouped.push(normalizeIngredient(current));
    index += 1;
  }

  return grouped.filter(Boolean);
}

function getSelectedIngredients() {
  if (!tagsContainer) return [];

  return Array.from(tagsContainer.querySelectorAll('.tag'))
    .map(tag => tag.dataset.ingredient || '')
    .filter(Boolean);
}

function updateIngredientSummary() {
  const selected = getSelectedIngredients();

  if (ingredientCounter) {
    ingredientCounter.textContent = `${selected.length} ingredient${selected.length === 1 ? '' : 's'} selected`;
  }

  if (selectedIngredientsPreview) {
    selectedIngredientsPreview.textContent = selected.length
      ? `Selected ingredients: ${selected.map(formatIngredient).join(', ')}`
      : 'No ingredients selected yet.';
  }
}

function setDetectedMessage(message) {
  const resultsDiv = document.getElementById('detected-results');
  if (resultsDiv) {
    resultsDiv.textContent = message;
  }
}

function getDetectionModelType() {
  return document.getElementById('detection-model')?.value || 'single';
}

function addTag(text = ingredientInput?.value?.trim() || '') {
  const normalized = normalizeIngredient(text);
  if (!normalized || !tagsContainer) return false;

  const exists = getSelectedIngredients().includes(normalized);
  if (exists) {
    if (ingredientInput) ingredientInput.value = '';
    return false;
  }

  const tag = document.createElement('span');
  tag.classList.add('tag');
  tag.dataset.ingredient = normalized;
  tag.innerHTML = `
    <span>${formatIngredient(normalized)}</span>
    <button type="button" aria-label="Remove ingredient">
      <i class="fas fa-times"></i>
    </button>
  `;

  tag.querySelector('button').addEventListener('click', () => {
    tag.remove();
    updateIngredientSummary();
  });

  tagsContainer.appendChild(tag);

  if (ingredientInput) ingredientInput.value = '';
  updateIngredientSummary();
  return true;
}

function addTagsFromText(text = '') {
  return parseIngredientItems(text)
    .filter(item => addTag(item))
    .map(item => formatIngredient(item));
}

function addDetectedIngredients(items = [], sourceLabel = 'Image') {
  const added = [];

  items.forEach(item => {
    if (addTag(item)) {
      added.push(formatIngredient(item));
    }
  });

  if (!items.length) {
    setDetectedMessage(`No ingredients detected from ${sourceLabel.toLowerCase()}.`);
    return;
  }

  if (added.length) {
    setDetectedMessage(`${sourceLabel} detected and added: ${added.join(', ')}`);
  } else {
    setDetectedMessage(`${sourceLabel} detected ingredients, but they are already in the ingredient bar.`);
  }
}

if (addBtn) addBtn.addEventListener('click', () => {
  const added = addTagsFromText(ingredientInput?.value || '');
  if (added.length) {
    setDetectedMessage(`Added to ingredient bar: ${added.join(', ')}`);
  }
  if (ingredientInput) ingredientInput.value = '';
});
if (ingredientInput) ingredientInput.addEventListener('keypress', e => {
  if (e.key === 'Enter') {
    const added = addTagsFromText(ingredientInput.value);
    if (added.length) {
      setDetectedMessage(`Added to ingredient bar: ${added.join(', ')}`);
    }
    ingredientInput.value = '';
  }
});
updateIngredientSummary();

// Voice Input
const micBtn = document.getElementById('voice-ingredient') || document.querySelector('.mic');
if (micBtn) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let ingredientRecognition = null;
  let ingredientRecognitionActive = false;
  let ingredientRecognitionStoppedByUser = false;

  const resetVoiceButtonState = () => {
    ingredientRecognitionActive = false;
    micBtn.disabled = false;
    micBtn.classList.remove('is-listening');
  };

  const stopIngredientRecognition = () => {
    ingredientRecognitionStoppedByUser = true;
    if (ingredientRecognition) {
      try {
        ingredientRecognition.stop();
      } catch (error) {
        console.warn('Unable to stop voice recognition cleanly:', error);
      }
    }
    resetVoiceButtonState();
  };

  const startIngredientRecognition = async () => {
    if (!SpeechRecognition) return;

    if (!window.isSecureContext) {
      setDetectedMessage('Voice input needs a secure browser context. Open RecipeGenie on localhost or HTTPS and try again.');
      return;
    }

    if (ingredientRecognitionActive) {
      stopIngredientRecognition();
      setDetectedMessage('Voice input stopped.');
      return;
    }

    if (navigator.mediaDevices?.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
      } catch (error) {
        const permissionMessage = error?.name === 'NotAllowedError'
          ? 'Microphone permission was blocked. Allow microphone access in your browser and try again.'
          : 'Microphone access is unavailable on this device right now. Please check your browser permissions.';
        setDetectedMessage(permissionMessage);
        return;
      }
    }

    if (!ingredientRecognition) {
      ingredientRecognition = new SpeechRecognition();
      ingredientRecognition.lang = 'en-IN';
      ingredientRecognition.interimResults = true;
      ingredientRecognition.continuous = true;
      ingredientRecognition.maxAlternatives = 1;

      ingredientRecognition.onstart = () => {
        ingredientRecognitionStoppedByUser = false;
        ingredientRecognitionActive = true;
        micBtn.disabled = false;
        micBtn.classList.add('is-listening');
        setDetectedMessage('Listening... say ingredients like "tomato, onion, paneer and olive oil". Tap the mic again to stop.');
      };

      ingredientRecognition.onresult = event => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let index = event.resultIndex; index < event.results.length; index += 1) {
          const transcript = event.results[index]?.[0]?.transcript || '';
          if (event.results[index].isFinal) {
            finalTranscript += ` ${transcript}`;
          } else {
            interimTranscript += ` ${transcript}`;
          }
        }

        const cleanFinal = finalTranscript.trim();
        const cleanInterim = interimTranscript.trim();

        if (cleanInterim) {
          setDetectedMessage(`Listening: ${cleanInterim}`);
        }

        if (cleanFinal) {
          const added = addTagsFromText(cleanFinal);
          setDetectedMessage(
            added.length
              ? `Voice added: ${added.join(', ')}`
              : `I heard "${cleanFinal}", but those ingredients were already added or could not be separated.`
          );
        }
      };

      ingredientRecognition.onerror = event => {
        const errorName = event?.error || 'unknown';
        const errorMap = {
          'not-allowed': 'Microphone permission was denied. Allow microphone access in your browser and try again.',
          'service-not-allowed': 'Speech recognition is blocked in this browser. Try Chrome or Edge and allow microphone access.',
          'audio-capture': 'No microphone was detected. Connect a microphone and try again.',
          'network': 'Speech recognition had a network problem. Check your internet connection and try again.',
          'no-speech': 'No speech was detected. Speak ingredient names clearly and try again.',
          'aborted': 'Voice input was stopped before speech was captured.'
        };

        if (errorName !== 'aborted') {
          setDetectedMessage(errorMap[errorName] || 'Voice input failed. Please try again or type ingredients manually.');
        }

        resetVoiceButtonState();
      };

      ingredientRecognition.onend = () => {
        const shouldRestart = ingredientRecognitionActive && !ingredientRecognitionStoppedByUser;
        resetVoiceButtonState();

        if (shouldRestart) {
          try {
            ingredientRecognition.start();
          } catch (error) {
            console.warn('Voice recognition restart failed:', error);
            setDetectedMessage('Voice input stopped unexpectedly. Please tap the microphone and try again.');
          }
        }
      };
    }

    try {
      ingredientRecognitionStoppedByUser = false;
      ingredientRecognition.start();
    } catch (error) {
      if (String(error?.message || '').toLowerCase().includes('already started')) {
        return;
      }
      console.error('Voice recognition start failed:', error);
      setDetectedMessage('Voice input could not start. Please try again or type ingredients manually.');
      resetVoiceButtonState();
    }
  };

  if (!SpeechRecognition) {
    micBtn.disabled = true;
    micBtn.title = 'Voice input is not supported in this browser';
    setDetectedMessage('Voice input is not supported in this browser. Use Chrome or Edge, or type ingredients manually.');
  } else {
    micBtn.addEventListener('click', startIngredientRecognition);
  }
}

// Image Upload

// const imageInput = document.createElement('input');
// imageInput.type = 'file';
// imageInput.accept = 'image/*';
// if (uploadBtn) {
//   uploadBtn.addEventListener('click', () => imageInput.click());
// }

// Find Recipes
if (findBtn) {
  findBtn.addEventListener('click', async () => {
    const ingredients = getSelectedIngredients();
    const recipeDemand = document.getElementById('recipe-demand')?.value || '';

    if (ingredients.length === 0) {
      alert("Please add ingredients first");
      return;
    }

    if (loadingChip) {
      loadingChip.style.display = 'inline-flex';
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          ingredients,
          query: recipeDemand
        })
      });
      clearTimeout(timeoutId);

      const contentType = res.headers.get('content-type') || '';
      const payload = contentType.includes('application/json')
        ? await res.json()
        : { error: await res.text() };

      if (!res.ok) {
        throw new Error(payload.message || payload.error || `HTTP ${res.status}`);
      }

      const recs = Array.isArray(payload.recipes) ? payload.recipes : [];

      const grid = document.querySelector('.recipe-grid');
      grid.innerHTML = '';

      if (!recs.length) {
        grid.innerHTML = `
          <div class="empty-state">
            <h3>No recipe matched your ingredient bar.</h3>
            <p>Try fewer ingredients or detect another ingredient from image or camera.</p>
          </div>
        `;
      } else {
        recs.forEach(recipe => {
          const card = createRecipeCard(recipe);
          grid.appendChild(card);
        });
      }

      const resultsSummary = document.getElementById('results-summary');
      if (resultsSummary) {
        const preferredHealth = payload.demand_profile?.preferred_health;
        resultsSummary.textContent = recs.length
          ? `${recs.length} filtered recipe${recs.length === 1 ? '' : 's'} found from Firebase.${preferredHealth ? ` Preference matched: ${preferredHealth}.` : ''}`
          : 'No Firebase recipes were found for the selected ingredients.';
      }

    } catch (error) {
      console.error("Recommendation error:", error);
      const resultsSummary = document.getElementById('results-summary');
      if (resultsSummary) {
        resultsSummary.textContent = error.name === 'AbortError'
          ? 'Recipe search took too long. Please run the ingredient index backfill once, then search again.'
          : `There was a problem loading filtered recipes from Firebase. ${error.message || ''}`.trim();
      }
    }

    if (loadingChip) {
      loadingChip.style.display = 'none';
    }

  });
}


// Cooked buttons
document.addEventListener('click', async e => {
  if (e.target.classList.contains('cooked-btn')) {
    const uid = requireLoggedIn({
      title: 'Login to save cooked recipes',
      message: 'Sign in so RecipeGenie can save this meal to your dashboard, history, and health tracker.'
    });
    const recipeId = e.target.dataset.recipeId;
    if (!uid) {
      return;
    }

    if (!recipeId) {
      alert('Recipe information is missing. Please reload and try again.');
      return;
    }

    const cookButton = e.target;
    cookButton.disabled = true;
    cookButton.textContent = 'Saving...';

    try {
      const response = await fetch('/cooked', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: uid, recipe_id: recipeId })
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || payload.message || `HTTP ${response.status}`);
      }

      const feedbackBox = document.getElementById('cook-feedback');
      const recommendationBox = document.getElementById('healthy-recommendations');

      if (feedbackBox) {
        feedbackBox.style.display = 'block';
        feedbackBox.innerHTML = `
          <h3>Meal saved to your tracker</h3>
          <div class="tracker-stat-grid">
            <div class="tracker-stat">
              <span>Status</span>
              <strong>${payload.health_label || 'Moderate'}</strong>
            </div>
            <div class="tracker-stat">
              <span>Health score</span>
              <strong>${payload.health_score || 0}/100</strong>
            </div>
            <div class="tracker-stat">
              <span>Calories</span>
              <strong>${payload.nutrition?.calories || 0} kcal</strong>
            </div>
          </div>
          <div class="tracker-stat-grid" style="margin-top:0.7rem;">
            <div class="tracker-stat">
              <span>Protein</span>
              <strong>${payload.nutrition?.protein || 0} g</strong>
            </div>
            <div class="tracker-stat">
              <span>Fiber</span>
              <strong>${payload.nutrition?.fiber || 0} g</strong>
            </div>
            <div class="tracker-stat">
              <span>Update</span>
              <strong>${payload.notification ? 'Attention' : 'Saved'}</strong>
            </div>
          </div>
          <div class="tracker-note-scroll" style="margin-top:0.85rem;">
            <strong>Notes:</strong> ${(payload.nutrition_notes || []).join(', ') || 'Nutrition data saved'}
            ${payload.notification ? `<p style="color:#c62828; margin-top:0.65rem;"><strong>Warning:</strong> ${payload.notification}</p>` : '<p style="margin-top:0.65rem; color:var(--secondary);"><strong>Good:</strong> Dashboard and health tracker updated successfully.</p>'}
          </div>
        `;
      }

      if (recommendationBox) {
        if (Array.isArray(payload.recommendations) && payload.recommendations.length) {
          recommendationBox.style.display = 'block';
          recommendationBox.innerHTML = `
            <h3>Healthy recipes for your next meal</h3>
            <div class="summary-recommendations">
            ${payload.recommendations.map(recipe => `
              <a href="/recipe-detail/${recipe.recipe_id}" class="summary-recipe-link">
                <strong>${recipe.name}</strong>
                <span>${recipe.reason}</span>
              </a>
            `).join('')}
            </div>
          `;
        } else {
          recommendationBox.style.display = 'none';
        }
      }

      cookButton.textContent = 'Saved To Tracker';
      loadDashboardReport();
      loadHealthReport();
    } catch (error) {
      alert(`Unable to save cooked recipe: ${error.message}`);
      cookButton.disabled = false;
      cookButton.textContent = 'Cooked This';
    }
  }
});

// History fetch
if (location.pathname.includes('history')) {
  (async () => {
    const uid = getCurrentUserId();
    const container = document.querySelector('.history-container') || document.getElementById('history-list');
    if (!container) return;

    if (!uid) {
      container.innerHTML = `
        <div class="history-empty">
          ${buildInlineLoginPrompt(
            'Login to view cooking history',
            'Your cooked recipes, health tags, and quick re-cook actions will appear here after you sign in.'
          )}
        </div>
      `;
      return;
    }

    if (uid) {
      const res = await fetch(`/history/${uid}`);
      const hist = await res.json();
      const sortedHistory = Array.isArray(hist)
        ? [...hist].sort((left, right) => {
            const leftTime = new Date(left?.cooked_at || left?.date || 0).getTime();
            const rightTime = new Date(right?.cooked_at || right?.date || 0).getTime();
            return rightTime - leftTime;
          })
        : [];
      container.innerHTML = '';

      if (!sortedHistory.length) {
        container.innerHTML = '<div class="history-empty">Cook a recipe to start building your cooking history.</div>';
        return;
      }

      sortedHistory.forEach(item => {
        const recipe = item.recipe || {};
        const healthType = recipe.health_label || recipe.category || 'Moderate';
        const imageUrl = getRecipeImageUrl(recipe);
        const cookedStamp = item.cooked_at || item.date;
        const cookedLabel = cookedStamp
          ? new Date(cookedStamp).toLocaleString([], {
              year: 'numeric',
              month: 'numeric',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit'
            })
          : 'Recently cooked';
        const div = document.createElement('div');
        div.classList.add('history-card');
        div.innerHTML = `
          <img src="${imageUrl}" alt="${recipe.name || 'Recipe'}" onerror="this.src='${DEFAULT_RECIPE_IMAGE}'">
          <div class="history-card-body">
            <div class="history-meta">
              <span class="history-date">${cookedLabel}</span>
              <span class="badge ${healthType.toLowerCase().replace(/\s+/g, '-')}">${healthType}</span>
            </div>
            <h3 style="margin-bottom:0.45rem; color:var(--secondary);">${recipe.name || 'Recipe'}</h3>
            <p style="color:var(--gray); margin-bottom:1rem;">Health score ${recipe.health_score || 0} • ${recipe.nutrition?.calories || 0} kcal</p>
            <div style="display:flex; gap:0.75rem; flex-wrap:wrap;">
              <button class="btn primary cooked-btn" data-recipe-id="${item.recipe_id}">Cook Again</button>
              <a href="/recipe-detail/${item.recipe_id}" class="btn" style="background:#f3eadf;">Open Recipe</a>
            </div>
          </div>
        `;
        container.appendChild(div);
      });
    }
  })();
}

////////////////////////////////////////////////////////////////////////////

// static/js/app.js
// ... your existing auth, menu toggle, logout code ...
let currentPage = 1;
let lastDocId = null;
let lastRecipeId = null;
let isLoading = false;
let hasMore = true;
let recipesAbortController = null;
let recipesRequestSeq = 0;

function createRecipeCard(recipe) {

  const card = document.createElement('div');
  card.classList.add('recipe-card');
  const hasMatchData = Array.isArray(recipe.matched_ingredients) || recipe.matching_score;
  const isLiked = recipe.isFavorite === true;
  const ingredients = Array.isArray(recipe.ingredients)
    ? recipe.ingredients
    : (typeof recipe.ingredients === "string" ? [recipe.ingredients] : []);
  const healthType = recipe.health_label || recipe.category || 'Moderate';
  const imageUrl = getRecipeImageUrl(recipe);

  card.innerHTML = `
    <div class="card-image-wrap">
      <img
        class="card-image"
        src="${imageUrl}"
        alt="${recipe.name}"
        onerror="this.src='${DEFAULT_RECIPE_IMAGE}'"
      >
      <span class="badge ${healthType.toLowerCase().replace(/\s+/g, '-')} card-type-badge">
        ${healthType}
      </span>
    </div>

    <div class="card-content">
      <h3>${recipe.name}</h3>

      ${hasMatchData ? `
        <p class="card-match-text">
          ${Math.round(recipe.matching_score || 0)}% match
          ${Array.isArray(recipe.matched_ingredients) && recipe.matched_ingredients.length ? ` • ${recipe.matched_ingredients.map(formatIngredient).join(", ")}` : ''}
        </p>
      ` : `
        <p class="card-match-text">Estimated health type: ${healthType}</p>
      `}

      <div class="buttons">
        <button
          class="btn view-ingredients-btn"
          type="button"
          data-recipe-name="${recipe.name}"
          title="View ingredients"
        >
          View Ingredients
        </button>

        <button class="like-btn ${isLiked ? 'liked' : ''}" data-recipe-id="${recipe.recipe_id}" title="Save to favorites">
          <i class="fas fa-heart"></i> ${isLiked ? 'Liked' : 'Favorite'}
        </button>

        <a href="/recipe-detail/${recipe.recipe_id}" class="btn primary">
          ${hasMatchData ? 'Cook Recipe' : 'View Recipe'}
        </a>
      </div>
    </div>
  `;

  const ingredientsButton = card.querySelector('.view-ingredients-btn');
  if (ingredientsButton) {
    ingredientsButton.addEventListener('click', () => {
      openIngredientsDialog(recipe.name, ingredients);
    });
  }

  return card;
}

// ==================================

async function loadRecipes(reset = false) {

  if (reset && recipesAbortController) {
    recipesAbortController.abort();
  }

  if (reset) {
    currentPage = 1;
    lastDocId = null;
    lastRecipeId = null;
    hasMore = true;
    const grid = document.querySelector('.recipe-grid');
    const noMore = document.getElementById('no-more');
    if (grid) grid.innerHTML = '';
    if (noMore) noMore.style.display = 'none';
  }

  // Prevent multiple calls
  if (isLoading && !reset) return;
  if (!hasMore) return;
  isLoading = true;
  const requestId = ++recipesRequestSeq;
  const controller = new AbortController();
  recipesAbortController = controller;

  // Get UI elements safely
  const loading = document.getElementById('loading');
  const noMore = document.getElementById('no-more');
  const grid = document.querySelector('.recipe-grid');

  // Show loading
  if (loading) loading.style.display = 'block';
  if (noMore) noMore.style.display = 'none';

  // Get filters
  const search = document.getElementById('search-input')?.value || '';
  const cuisine = document.getElementById('cuisine-select')?.value || 'All';
  const highRated = document.getElementById('high-rated')?.checked || false;

  // Build URL
  let url = `/get-recipes?cuisine=${encodeURIComponent(cuisine)}&search=${encodeURIComponent(search)}&high_rated=${highRated}&limit=50`;

  if (!reset && lastRecipeId) {
    url += `&last_doc_id=${encodeURIComponent(lastRecipeId)}`;
  }

  try {

    // ✅ FETCH API (IMPORTANT FIX)
    const res = await fetch(url, { signal: controller.signal });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    if (requestId !== recipesRequestSeq) return;

    console.log("API DATA:", data);

    // Append recipes safely
    if (data.recipes && Array.isArray(data.recipes)) {
      data.recipes.forEach(recipe => {
        grid.appendChild(createRecipeCard(recipe));
      });
    }

    // Pagination update
    lastRecipeId = data.last_doc_id || null;
    hasMore = data.has_more === true;

    // No more data
    if (!hasMore && grid && grid.children.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <h3>No recipes found for this cuisine.</h3>
          <p>Try All Cuisines or choose another cuisine from the dataset.</p>
        </div>
      `;
    } else if (!hasMore && noMore) {
      noMore.style.display = 'block';
    }

  } catch (err) {
    if (err.name === 'AbortError') return;

    console.error('Error loading recipes:', err);

    if (grid) {
      grid.innerHTML += `
        <p style="color:red; text-align:center;">
          Error loading recipes. Please try again.
        </p>
      `;
    }

  } finally {

    if (requestId === recipesRequestSeq) {
      isLoading = false;

      if (loading) loading.style.display = 'none';
    }
  }
}

// =======================

function renderGeneratedRecipe(data) {
  const nutrition = data.nutrition || {};
  const notes = Array.isArray(data.nutrition_notes) ? data.nutrition_notes : [];
  return `
    <article class="generated-recipe-card">
      <div class="generated-recipe-header">
        <div>
          <span class="generate-eyebrow">Generated recipe</span>
          <h2>${data.name || 'Smart Recipe'}</h2>
          <p>${data.cooking_time || '20 minutes'} cooking time</p>
        </div>
        <span class="generated-health-badge">${data.health_label || 'Moderate'} &bull; ${Math.round(data.health_score || 0)}</span>
      </div>

      <div class="generated-recipe-grid">
        <section>
          <h3>Ingredients</h3>
          <ul class="generated-list">
            ${(data.ingredients || []).map(item => `<li>${item}</li>`).join('')}
          </ul>
        </section>
        <section>
          <h3>Nutrition estimate</h3>
          <div class="generated-nutrition">
            <span><strong>${Math.round(nutrition.calories || 0)}</strong> kcal</span>
            <span><strong>${Math.round(nutrition.protein || 0)}g</strong> protein</span>
            <span><strong>${Math.round(nutrition.fiber || 0)}g</strong> fiber</span>
            <span><strong>${Math.round(nutrition.fat || 0)}g</strong> fat</span>
          </div>
        </section>
      </div>

      <section>
        <h3>Cooking steps</h3>
        <ol class="generated-steps">
          ${(data.steps || []).map(step => `<li>${step}</li>`).join('')}
        </ol>
      </section>

      ${notes.length ? `<div class="generated-note">${notes.slice(0, 2).join(' ')}</div>` : ''}
    </article>
  `;
}


async function generateRecipe() {
    const input = document.getElementById("ingredients")?.value?.trim() || "";
    const output = document.getElementById("output");
    const selectedIngredients = getSelectedIngredients();
    const typedIngredients = parseIngredientItems(input);
    const ingredients = Array.from(new Set([...selectedIngredients, ...typedIngredients]));

    if (!ingredients.length) {
        if (output) {
          output.innerHTML = '<div class="generated-empty"><h2>Add ingredients first</h2><p>Type, speak, upload an image, or capture from camera before generating.</p></div>';
        }
        return;
    }

    if (output) {
      output.innerHTML = '<div class="generated-empty"><h2>Generating your recipe...</h2><p>RecipeGenie is building steps and nutrition details.</p></div>';
    }

    try {
        const res = await fetch('/generate-recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ingredients })
        });

        const contentType = res.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await res.json()
            : { error: await res.text() };

        if (!res.ok) {
            throw new Error(data.error || `Server error ${res.status}`);
        }

        if (data.error) {
            output.innerHTML = `<div class="generated-empty"><h2>Unable to generate recipe</h2><p>${data.error}</p></div>`;
            return;
        }

        output.innerHTML = `
            <h2>${data.name}</h2>

            <h3>🧾 Ingredients:</h3>
            <ul>
                ${data.ingredients.map(i => `<li>${i}</li>`).join("")}
            </ul>

            <h3>👨‍🍳 Steps:</h3>
            <ol>
                ${data.steps.map(s => `<li>${s}</li>`).join("")}
            </ol>

            <p><b>⏱ Cooking Time:</b> ${data.cooking_time}</p>
        `;

        output.innerHTML = renderGeneratedRecipe(data);

    } catch (err) {
        console.error(err);
        output.innerHTML = `<div class="generated-empty"><h2>Failed to connect to server</h2><p>${err.message || 'Please try again.'}</p></div>`;
    }
}

window.generateRecipe = generateRecipe;

document.getElementById('generate-recipe-form')?.addEventListener('submit', event => {
  event.preventDefault();
  generateRecipe();
});

async function loadHealthReport(){

const uid = getCurrentUserId()

if(!uid) {
const suggestionsBox = document.getElementById("health-suggestions")
if (suggestionsBox) {
  suggestionsBox.textContent = "Login to track your meals, get healthy reminders, and see personalized recipe suggestions."
}

const recommendationGrid = document.getElementById("healthy-recommendations-grid")
if (recommendationGrid) {
  recommendationGrid.innerHTML = buildInlineLoginPrompt(
    'Login to unlock health recommendations',
    'RecipeGenie will recommend healthier next meals after it can track your cooked recipes.'
  )
}

const recentMealsGrid = document.getElementById("recent-meals-grid")
if (recentMealsGrid) {
  recentMealsGrid.innerHTML = buildInlineLoginPrompt(
    'Login to track recent meals',
    'Your saved nutrition summary and recent cooked recipes will appear here.'
  )
}
return
}

const res = await fetch(`/health-report/${uid}`)

const data = await res.json()

if (document.getElementById("healthy-count")) {
  document.getElementById("healthy-count").innerText = data.healthy
}
if (document.getElementById("moderate-count")) {
  document.getElementById("moderate-count").innerText = data.moderate
}
if (document.getElementById("fast-count")) {
  document.getElementById("fast-count").innerText = data.fastfood
}

if (document.getElementById("health-score")) {
  document.getElementById("health-score").innerText =
  `Health Score: ${data.health_score} (${data.status})`
}

const healthScoreValue = document.getElementById("health-score-value")
if (healthScoreValue) {
  healthScoreValue.innerText = data.health_score || 0
}

const healthScoreRing = document.getElementById("health-score-ring")
if (healthScoreRing) {
  const score = Math.max(0, Math.min(100, Number(data.health_score || 0)))
  const degrees = Math.round((score / 100) * 360)
  healthScoreRing.style.background = `conic-gradient(var(--secondary) 0deg, var(--secondary) ${degrees}deg, #ebe4d7 ${degrees}deg 360deg)`
}

if (document.getElementById("health-progress")) {
  document.getElementById("health-progress").style.width =
  Math.min(100,Math.max(0,data.health_score*5))+"%"
}

const suggestionsBox = document.getElementById("health-suggestions")
if (suggestionsBox) {
  suggestionsBox.innerHTML = data.warning
    ? `Try a healthy next meal. ${data.warning}`
    : "Your recent meals look balanced. Keep mixing fiber-rich and protein-rich foods."
}

const warningBox = document.getElementById("health-warning")
if (warningBox) {
  if (data.warning || data.last_notification) {
    warningBox.style.display = "block"
    warningBox.textContent = data.warning || data.last_notification
  } else {
    warningBox.style.display = "none"
  }
}

const recommendationGrid = document.getElementById("healthy-recommendations-grid")
if (recommendationGrid) {
  const recommendations = Array.isArray(data.healthy_recommendations) ? data.healthy_recommendations : []
  recommendationGrid.innerHTML = recommendations.length
    ? recommendations.map(recipe => `
        <div class="insight-item">
          <div class="insight-copy">
            <div class="insight-meta">
              <span class="insight-tag">${recipe.health_label || 'Healthy Choice'}</span>
              <span class="insight-score">Score ${Math.round(recipe.health_score || 0)}</span>
            </div>
            <h3>${recipe.name}</h3>
            <p>${recipe.reason}</p>
          </div>
          <a href="/recipe-detail/${recipe.recipe_id}" class="btn primary insight-cta">Cook This</a>
        </div>
      `).join("")
    : '<div class="insight-item"><p>No healthy recommendations available yet.</p></div>'
}

const recentMealsGrid = document.getElementById("recent-meals-grid")
if (recentMealsGrid) {
  const meals = Array.isArray(data.recent_meals) ? data.recent_meals : []
  recentMealsGrid.innerHTML = meals.length
    ? meals.map(meal => `
        <div class="insight-item recent-meal-card">
          <div class="insight-copy">
            <div class="insight-meta">
              <span class="insight-tag">${meal.health_label || "Moderate"}</span>
              <span class="insight-score">${meal.cooked_at ? new Date(meal.cooked_at).toLocaleDateString() : "Recently cooked"}</span>
            </div>
            <h3>${meal.recipe_name || "Recipe"}</h3>
          </div>
          <div class="recent-meal-grid">
            <div class="recent-meal-stat">
              <span>Calories</span>
              <strong>${meal.nutrition?.calories || 0} kcal</strong>
            </div>
            <div class="recent-meal-stat">
              <span>Protein</span>
              <strong>${meal.nutrition?.protein || 0} g</strong>
            </div>
            <div class="recent-meal-stat">
              <span>Fiber</span>
              <strong>${meal.nutrition?.fiber || 0} g</strong>
            </div>
          </div>
        </div>
      `).join("")
    : '<div class="insight-item"><p>No meals tracked yet. Cook a recipe to start monitoring.</p></div>'
}

}

async function loadDashboardReport() {

const uid = getCurrentUserId()

if(!document.getElementById("dashboard-total-cooked")) return

if(!uid) {
const smartTip = document.getElementById("dashboard-smart-tip")
if (smartTip) {
  smartTip.textContent = "Login to save meals, track health score, and build your cooking dashboard."
}

const tipCard = document.getElementById("dashboard-tip-card")
if (tipCard) {
  tipCard.innerHTML = buildInlineLoginPrompt(
    'Login to start your dashboard',
    'RecipeGenie shows favorites, recent meals, and health insights once your account is connected.'
  )
}

const recentMeals = document.getElementById("dashboard-recent-meals")
if (recentMeals) {
  recentMeals.innerHTML = buildInlineLoginPrompt(
    'Login to see cooking activity',
    'Your cooked recipes and meal timeline will appear here after you sign in.'
  )
}

const favoritesList = document.getElementById("dashboard-favorites-list")
if (favoritesList) {
  favoritesList.innerHTML = buildInlineLoginPrompt(
    'Login to see favorite recipes',
    'Liked recipes will appear here with direct links to recipe details once you sign in.'
  )
}
return
}

const res = await fetch(`/dashboard-report/${uid}`)
const data = await res.json()

document.getElementById("dashboard-total-cooked").innerText = data.total_recipes_cooked || 0
document.getElementById("dashboard-healthy-count").innerText = data.healthy || 0
document.getElementById("dashboard-moderate-count").innerText = data.moderate || 0
document.getElementById("dashboard-unhealthy-count").innerText = data.unhealthy || 0
document.getElementById("dashboard-health-score").innerText = data.health_score || 0
document.getElementById("dashboard-favorites-count").innerText = data.favorite_count || 0

const smartTip = document.getElementById("dashboard-smart-tip")
if (smartTip) {
  smartTip.textContent = data.smart_tip || "Track cooked recipes, health score, and your meal pattern."
}

const tipCard = document.getElementById("dashboard-tip-card")
if (tipCard) {
  tipCard.textContent = data.smart_tip || "Balanced cooking starts with one healthier next meal."
}

const warningCard = document.getElementById("dashboard-warning")
if (warningCard) {
  if (data.warning) {
    warningCard.style.display = "block"
    warningCard.textContent = data.warning
  } else {
    warningCard.style.display = "none"
  }
}

const scoreRing = document.getElementById("dashboard-score-ring")
if (scoreRing) {
  const score = Math.max(0, Math.min(100, Number(data.health_score || 0)))
  const degrees = Math.round((score / 100) * 360)
  scoreRing.style.background = `conic-gradient(var(--secondary) 0deg, var(--secondary) ${degrees}deg, #efe5d7 ${degrees}deg 360deg)`
}

const recentMeals = document.getElementById("dashboard-recent-meals")
if (recentMeals) {
  const meals = Array.isArray(data.recent_meals) ? data.recent_meals : []
  recentMeals.innerHTML = meals.length
    ? meals.map(meal => `
        <div class="dashboard-list-item">
          <strong style="display:block; color:var(--secondary);">${meal.recipe_name || "Recipe"}</strong>
          <span style="display:block; margin-top:0.25rem; color:var(--gray);">${meal.health_label || "Moderate"} meal</span>
          <span style="display:block; margin-top:0.2rem; color:var(--gray);">Health score ${meal.health_score || 0}</span>
          <span style="display:block; margin-top:0.2rem; color:var(--gray);">${meal.cooked_at ? new Date(meal.cooked_at).toLocaleDateString() : ""}</span>
        </div>
      `).join("")
    : '<div class="dashboard-list-item">Cook a recipe to start seeing your meal history.</div>'
}

loadFavorites()

}

console.log(document.getElementById("recipes-container"));
console.log(document.getElementById("favorites-container"));

// Load favorites
async function loadFavorites() {
  const uid = getCurrentUserId();
  const favoritesList = document.getElementById('dashboard-favorites-list');
  if (!uid || !favoritesList) return;

  try {
    const res = await fetch(`/favorites/${uid}`);
    if (!res.ok) throw new Error('Failed to load favorites');

    const favorites = await res.json();
    favoritesList.innerHTML = favorites.length === 0
      ? '<div class="dashboard-list-item">You have not liked any recipes yet. Save a recipe to see it here.</div>'
      : favorites.map(fav => {
          const recipeName = fav.name || 'Recipe';
          const healthType = fav.health_label || fav.category || 'Moderate';
          const calories = Math.round(fav.nutrition?.calories || 0);
          const healthScore = Math.round(fav.health_score || 0);
          const recipeId = fav.recipe_id || '';
          return `
            <article class="dashboard-favorite-item">
              <div class="dashboard-favorite-top">
                <div>
                  <strong>${recipeName}</strong>
                  <div class="dashboard-favorite-meta">
                    <span>Health score ${healthScore}</span>
                    <span>${calories} kcal</span>
                  </div>
                </div>
                <span class="badge ${healthType.toLowerCase().replace(/\s+/g, '-')}">${healthType}</span>
              </div>
              <div class="dashboard-favorite-actions">
                <a href="/recipe-detail/${recipeId}" class="btn primary">View Recipe</a>
              </div>
            </article>
          `;
        }).join('');
  } catch (err) {
    console.error('Favorites error:', err);
    favoritesList.innerHTML = '<div class="dashboard-list-item">Unable to load favorite recipes right now.</div>';
  }
}


// // image detection   
// async function detectIngredients(){

//     const input = document.getElementById("imageUpload")

//     if(input.files.length === 0){
//         alert("Please upload image")
//         return
//     }

//     const formData = new FormData()
//     formData.append("image", input.files[0])

//     const res = await fetch("/detect-ingredients",{
//         method:"POST",
//         body:formData
//     })

//     const data = await res.json()

//     const resultDiv = document.getElementById("detected-results")

//     resultDiv.innerHTML = ""

//     data.ingredients.forEach(item=>{

//         const p = document.createElement("p")

//         p.innerText =
//             item.ingredient +
//             " (" +
//             (item.confidence * 100).toFixed(1) +
//             "%)"

//         resultDiv.appendChild(p)

//     })

// }

async function captureImage() {

    const video = document.getElementById("camera");
    const canvas = document.getElementById("canvas");

    const ctx = canvas.getContext("2d");

    if (!video || !video.srcObject) {
        alert("Start the camera first");
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0);

    canvas.toBlob(async function(blob) {

        const formData = new FormData();
        formData.append("image", blob, "capture.jpg");
        const modelType = getDetectionModelType();
        formData.append("model_type", modelType);
        setDetectedMessage(`Detecting camera image with ${modelType} model...`);

        try {
            const res = await fetch("/detect-ingredients", {
                method: "POST",
                body: formData
            });

            const data = await res.json();
            if (!res.ok || data.error) {
                throw new Error(data.error || `Detection failed with HTTP ${res.status}`);
            }
            addDetectedIngredients(data.ingredients || [], `${formatIngredient(modelType)} camera model`);
        } catch (error) {
            console.error("Camera detection error:", error);
            setDetectedMessage(`Camera detection failed: ${error.message}`);
        }

    });
}

async function startCamera() {

    const video = document.getElementById("camera");
    const placeholder = document.getElementById("camera-placeholder");

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });

        video.srcObject = stream;
        video.style.display = "block";
        if (placeholder) {
            placeholder.style.display = "none";
        }
        setDetectedMessage("Camera started. Capture an image to detect ingredients.");

    } catch (err) {
        alert("Camera access denied");
    }
}

window.captureImage = captureImage;
window.startCamera = startCamera;

function detectIngredients() {

    const imageUpload = document.getElementById("imageUpload");

    if (!imageUpload.files.length) {
        alert("Please upload an image first");
        return;
    }

    const formData = new FormData();
    formData.append("image", imageUpload.files[0]);
    const modelType = getDetectionModelType();
    formData.append("model_type", modelType);
    setDetectedMessage(`Detecting uploaded image with ${modelType} model...`);

    fetch("/detect-ingredients", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        addDetectedIngredients(data.ingredients || [], `${formatIngredient(modelType)} image model`);

    })
    .catch(err => {
        console.error(err);
        setDetectedMessage(`Image detection failed: ${err.message}`);
    });
}

window.detectIngredients = detectIngredients;

// function detectIngredients() {

//     const imageUpload = document.getElementById("imageUpload");
//     const resultsDiv = document.getElementById("detected-results");

//     if (!imageUpload.files.length) {
//         alert("Please upload an image first");
//         return;
//     }

//     const formData = new FormData();
//     formData.append("image", imageUpload.files[0]);

//     fetch("/detect-ingredients", {
//         method: "POST",
//         body: formData
//     })
//     .then(response => response.json())
//     .then(data => {

//         resultsDiv.innerHTML = "";

//         if (!data.ingredients || data.ingredients.length === 0) {
//             resultsDiv.innerHTML = "No ingredients detected";
//             return;
//         }

//         data.ingredients.forEach(item => {

//             const p = document.createElement("p");
//             p.innerText = item.ingredient + " (" + item.confidence.toFixed(2) + ")";

//             resultsDiv.appendChild(p);

//         });

//     })
//     .catch(error => {
//         console.error("Error:", error);
//     });

// }

// window.detectIngredients = detectIngredients;

const startCameraBtn = document.getElementById("startCamera");
const captureBtn = document.getElementById("captureBtn");
const detectBtn = document.getElementById("detect-image-ingredients");

const video = document.getElementById("camera");
const canvas = document.getElementById("canvas");

const imageUpload = document.getElementById("imageUpload");
const resultsDiv = document.getElementById("detected-results");

let stream;

if (startCameraBtn) {
    startCameraBtn.addEventListener("click", startCamera);
}

if (captureBtn) {
    captureBtn.addEventListener("click", captureImage);
}

if (detectBtn) {
    detectBtn.addEventListener("click", detectIngredients);
}


/* -------------------------
START CAMERA
--------------------------*/

// startCameraBtn.addEventListener("click", async () => {

//     try {

//         stream = await navigator.mediaDevices.getUserMedia({
//             video: true
//         });

//         video.srcObject = stream;

//         video.style.display = "block";
//         captureBtn.style.display = "inline-block";

//     } catch (err) {

//         alert("Camera access denied");

//     }

// });



/* -------------------------
CAPTURE IMAGE
--------------------------*/

// captureBtn.addEventListener("click", async () => {

//     const ctx = canvas.getContext("2d");

//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;

//     ctx.drawImage(video, 0, 0);


//     canvas.toBlob(async function(blob) {

//         const formData = new FormData();

//         formData.append("image", blob, "capture.jpg");


//         const res = await fetch("/detect-ingredients", {

//             method: "POST",
//             body: formData

//         });

//         const data = await res.json();

//         displayResults(data.ingredients);

//     });

// });



/* -------------------------
UPLOAD IMAGE
--------------------------*/

// detectBtn.addEventListener("click", async () => {

//     if (imageUpload.files.length === 0) {
//         alert("Please select image");
//         return;
//     }else{
//       const formData = new FormData();
//       formData.append("image", imageUpload.files[0]);

//       const res = await fetch("/detect-ingredients", {
//         method: "POST",
//         body: formData
//       });

//       const data = await res.json();

//       displayResults(data.ingredients);
//     }

    

// });



/* -------------------------
SHOW RESULTS
--------------------------*/
function displayResults(recipes) {
    console.log(recipes)
    const grid = document.querySelector(".recipe-grid")

    grid.innerHTML = ""

    recipes.forEach(recipe => {

        const card = document.createElement("div")

        card.className = "recipe-card"

        card.innerHTML = `

<img src="/static/images/${recipe.name}.jpg">

<h3>${recipe.name}</h3>

<p>${Math.round(recipe.matching_score)}% Match</p>

<a href="/recipe-detail/${recipe.recipe_id}" class="btn primary">
View Recipe
</a>

`

        grid.appendChild(card)

    })

}

function openIngredientsDialog(recipeName, ingredients) {
  const existingOverlay = document.querySelector('.ingredients-dialog-overlay');
  if (existingOverlay) {
    existingOverlay.remove();
  }

  const overlay = document.createElement('div');
  overlay.className = 'ingredients-dialog-overlay';

  const dialog = document.createElement('div');
  dialog.className = 'ingredients-dialog';
  dialog.innerHTML = `
    <div class="ingredients-dialog-header">
      <div>
        <span class="ingredients-dialog-eyebrow">Recipe Ingredients</span>
        <h3>${recipeName}</h3>
      </div>
      <button type="button" class="ingredients-dialog-close" aria-label="Close ingredients dialog">
        <i class="fas fa-times"></i>
      </button>
    </div>
    <div class="ingredients-dialog-body">
      ${
        Array.isArray(ingredients) && ingredients.length
          ? ingredients.map(item => `<div class="ingredients-dialog-item">${item}</div>`).join('')
          : '<div class="ingredients-dialog-item">No ingredients available.</div>'
      }
    </div>
  `;

  overlay.appendChild(dialog);
  document.body.appendChild(overlay);

  const closeDialog = () => overlay.remove();
  overlay.addEventListener('click', event => {
    if (event.target === overlay) {
      closeDialog();
    }
  });
  dialog.querySelector('.ingredients-dialog-close')?.addEventListener('click', closeDialog);
}

// function displayResults(items) {

//     resultsDiv.innerHTML = "";

//     items.forEach(item => {

//         const p = document.createElement("p");

//         p.innerText = item.ingredient + " (" + item.confidence.toFixed(2) + ")";

//         resultsDiv.appendChild(p);

//     });

// }
//
// Infinite scroll trigger
let scrollTimeout;

window.addEventListener('scroll', () => {
  if (!document.getElementById('search-input')) return;

  if (scrollTimeout) return;

  scrollTimeout = setTimeout(() => {

    if (!isLoading && hasMore &&
        (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300)) {
      loadRecipes();
    }

    scrollTimeout = null;

  }, 200);

});

// Filter events
document.getElementById('apply-filter')?.addEventListener('click', () => loadRecipes(true));
document.getElementById('search-input')?.addEventListener('keypress', e => {
  if (e.key === 'Enter') loadRecipes(true);
});
document.getElementById('high-rated')?.addEventListener('change', () => loadRecipes(true));
document.getElementById('cuisine-select')?.addEventListener('change', () => loadRecipes(true));

// Like / Unlike handler
document.addEventListener('click', async e => {
  const btn = e.target.closest('.like-btn');
  if (!btn) return;

  const uid = requireLoggedIn({
    title: 'Login to save favorites',
    message: 'Sign in so RecipeGenie can save this recipe in your favorites and use it in your dashboard insights.'
  });
  if (!uid) {
    return;
  }

  const recipeId = btn.dataset.recipeId;
  const isLiked = btn.classList.contains('liked');
  const endpoint = isLiked ? '/unlike-recipe' : '/like-recipe';

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: uid, recipe_id: recipeId })
    });

    if (res.ok) {
      btn.classList.toggle('liked');
      btn.innerHTML = `<i class="fas fa-heart"></i> ${isLiked ? 'Like' : 'Liked'}`;
      loadFavorites(); // refresh favorites section
    }
  } catch (err) {
    console.error('Like error:', err);
  }
});

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('search-input')) {
      loadRecipes(true);
      // loadFavorites();
    }
    loadDashboardReport();
    loadHealthReport();

});

// Animate progress bars
document.querySelectorAll('.progress').forEach(bar => {
  setTimeout(() => {
    bar.style.width = bar.parentElement.dataset.width || bar.style.width;
  }, 500);
});


////////////////////////////////////////////////////////////////////////////


// Main load function
// async function loadRecipes(reset = false) {
//   if (isLoading || !hasMore) return;
  
//   isLoading = true;
//   document.getElementById('loading-more').style.display = 'block';
//   document.getElementById('no-more').style.display = 'none';

//   if (reset) {
//     currentPage = 1;
//     lastDocId = null;
//     document.querySelector('.recipe-grid').innerHTML = '';
//   }

//   const search = document.getElementById('search-input')?.value || '';
//   const state = document.getElementById('state-select')?.value || 'All';
//   const highRated = document.getElementById('high-rated')?.checked || false;

//   const url = `/get-recipes?state=${encodeURIComponent(state)}&search=${encodeURIComponent(search)}&high_rated=${highRated}&limit=50${lastDocId ? `&last_doc_id=${lastDocId}` : ''}`;
  
//   try {
//     const res = await fetch(url);
//     const data = await res.json();

//     const grid = document.querySelector('.recipe-grid');

//     data.recipes.forEach(r => {
//       const card = document.createElement('div');
//       card.classList.add('recipe-card');
//       card.innerHTML = `
//         <img src="/static/images/${r.name.replace(/ /g, '_')}.jpg" alt="${r.name}" onerror="this.src='placeholder.jpg'">
//         <h3>${r.name}</h3>
//         <span class="badge ${r.category?.toLowerCase() || 'moderate'}">${r.category || 'Moderate'}</span>
//         <p>Rating: ${r.ratings || 'N/A'}</p>
//         <button class="like-btn" data-recipe-id="${r.recipe_id}">
//           <i class="fas fa-heart"></i> Like
//         </button>
//         <a href="/recipe-detail/${r.recipe_id}" class="btn primary">Cook This</a>
//       `;
//       grid.appendChild(card);
//     });

//     lastDocId = data.last_doc_id;
//     hasMore = data.has_more;

//     if (!hasMore) {
//       document.getElementById('no-more').style.display = 'block';
//     }

//   } catch (err) {
//     console.error('Error loading recipes:', err);
//   } finally {
//     isLoading = false;
//     document.getElementById('loading-more').style.display = 'none';
//   }
// }

// // Infinite scroll using Intersection Observer
// function setupInfiniteScroll() {
//   const sentinel = document.createElement('div');
//   sentinel.id = 'scroll-sentinel';
//   sentinel.style.height = '20px';
//   document.querySelector('.section').appendChild(sentinel);

//   const observer = new IntersectionObserver((entries) => {
//     if (entries[0].isIntersecting && !isLoading && hasMore) {
//       loadRecipes(false);  // load next page
//     }
//   }, { threshold: 0.1 });

//   observer.observe(sentinel);
// }

// // Load favorites
// async function loadFavorites() {
//   const uid = localStorage.getItem('uid');
//   if (!uid) return;

//   const res = await fetch(`/favorites/${uid}`);
//   const favorites = await res.json();

//   const favGrid = document.querySelector('.favorite-grid');
//   favGrid.innerHTML = '';

//   favorites.forEach(f => {
//     const card = document.createElement('div');
//     card.classList.add('recipe-card');
//     card.innerHTML = `
//       <img src="/static/images/${f.recipe.name.replace(/ /g, '_')}.jpg" alt="${f.recipe.name}">
//       <h3>${f.recipe.name}</h3>
//       <span class="badge ${f.recipe.category.toLowerCase()}">${f.recipe.category}</span>
//       <a href="/recipe-detail/${f.recipe.recipe_id}" class="btn primary">View & Cook</a>
//     `;
//     favGrid.appendChild(card);
//   });
// }

// // Like / Unlike handler
// document.addEventListener('click', async e => {
//   if (e.target.closest('.like-btn')) {
//     const btn = e.target.closest('.like-btn');
//     const uid = localStorage.getItem('uid');
//     const recipeId = btn.dataset.recipeId;

//     if (!uid) {
//       alert('Please login first');
//       return;
//     }

//     const isLiked = btn.classList.contains('liked');
//     const endpoint = isLiked ? '/unlike-recipe' : '/like-recipe';

//     await fetch(endpoint, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({ user_id: uid, recipe_id: recipeId })
//     });

//     btn.classList.toggle('liked');
//     btn.innerHTML = `<i class="fas fa-heart"></i> ${isLiked ? 'Like' : 'Liked'}`;
//     loadFavorites(); // refresh list
//   }
// });

// // Apply filters
// document.getElementById('apply-filter')?.addEventListener('click', loadRecipes);
// document.getElementById('search-input')?.addEventListener('keypress', e => {
//   if (e.key === 'Enter') loadRecipes();
// });

// // Initial load
// document.addEventListener('DOMContentLoaded', () => {
//   loadRecipes(true);
//   loadFavorites();
//   setupInfiniteScroll();
//   const searchInput = document.getElementById('search-input');
//   const stateSelect = document.getElementById('state-select');
//   const highRated = document.getElementById('high-rated');
//   const applyBtn = document.getElementById('apply-filter');

//   const reloadWithFilters = () => loadRecipes(true);

//   searchInput?.addEventListener('keypress', e => { if (e.key === 'Enter') reloadWithFilters(); });
//   stateSelect?.addEventListener('change', reloadWithFilters);
//   highRated?.addEventListener('change', reloadWithFilters);
//   applyBtn?.addEventListener('click', reloadWithFilters);
// });



