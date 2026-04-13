// Gujarat Smart Recipe Recommendation System - JavaScript

// Firebase Setup for Auth'

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';

import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged, updateProfile } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';

// Your web app's Firebase configuration

const firebaseConfig = {
  apiKey: "AIzaSyDCJsc1P1swgnDvqlejcjo9uq60BdxHmBI",
  authDomain: "recipe-recommendation-259bf.firebaseapp.com",
  databaseURL: "https://recipe-recommendation-259bf-default-rtdb.firebaseio.com",
  projectId: "recipe-recommendation-259bf",
  storageBucket: "recipe-recommendation-259bf.firebasestorage.app",
  messagingSenderId: "225689206362",
  appId: "1:225689206362:web:73dc41fc1bfdb22447e263",
  measurementId: "G-46CVPYZ0QZ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
// const analytics = getAnalytics(app);
const auth = getAuth(app);


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
  registerForm.addEventListener('submit', async e => {
    e.preventDefault();
    const name = document.querySelector('#full-name')?.value || document.querySelector('#reg-name')?.value;
    const email = document.querySelector('#reg-email')?.value;
    const password = document.querySelector('#password')?.value || document.querySelector('#reg-password')?.value;
    const confirm = document.querySelector('#confirm-password')?.value || document.querySelector('#reg-confirm')?.value;
    const errorEl = document.querySelector('#reg-error') || document.querySelector('.error');

    if (password !== confirm) {
      errorEl.textContent = 'Passwords do not match!';
      return;
    }

    const validation = validatePasswordStrength(password);
    if (!validation.isValid) {
      errorEl.innerHTML = validation.errors.join('<br>');
      return;
    }

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      if (name) await updateProfile(user, { displayName: name });

      const res = await fetch('/save-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid: user.uid,
          name: name,
          email: email
        })
      });
      localStorage.setItem("uid", user.uid);
      window.location.href = "/login";
    } catch (error) {
      errorEl.textContent = error.message;
    }
  });
}

// Login Form (for login.html)
const loginForm = document.querySelector('#login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const email = document.querySelector('#login-email')?.value || loginForm.querySelector('input[type="email"]').value;
    const password = document.querySelector('#login-password')?.value || loginForm.querySelector('input[type="password"]').value;
    const errorEl = document.querySelector('#login-error') || document.querySelector('.error');

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      localStorage.setItem("uid", user.uid);
      window.location.href = '/home';
    } catch (error) {
      errorEl.textContent = error.message;
    }
  });
}

// Auth state listener (updates navbar, etc.)
onAuthStateChanged(auth, (user) => {
  const loginLinks = document.querySelectorAll('.login-link');
  const registerLinks = document.querySelectorAll('.register-link');
  const logoutLink = document.querySelector('.logout-link');

  if (user) {
    // User logged in - hide login/register, show logout
    loginLinks.forEach(link => link.style.display = 'none');
    registerLinks.forEach(link => link.style.display = 'none');
    if (logoutLink) logoutLink.style.display = 'block';
    localStorage.setItem('uid', user.uid);  // For backend use
  } else {
    // User logged out - show login/register
    loginLinks.forEach(link => link.style.display = 'block');
    registerLinks.forEach(link => link.style.display = 'block');
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
  return String(text)
    .split(/[,;\n]+/)
    .map(item => item.trim())
    .filter(Boolean)
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

  if (!SpeechRecognition) {
    micBtn.disabled = true;
    micBtn.title = 'Voice input is not supported in this browser';
  } else {
    micBtn.addEventListener('click', () => {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-IN';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = e => {
        const transcript = e.results?.[0]?.[0]?.transcript || '';
        const added = addTagsFromText(transcript);
        setDetectedMessage(
          added.length
            ? `Voice added: ${added.join(', ')}`
            : 'Voice ingredient was already in the ingredient bar.'
        );
      };
      recognition.onerror = () => {
        setDetectedMessage('Voice input failed. Please try again or type the ingredient manually.');
      };
      recognition.start();
    });
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
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ingredients,
          query: recipeDemand
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const payload = await res.json();
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
        resultsSummary.textContent = 'There was a problem loading filtered recipes from Firebase.';
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
    const uid = localStorage.getItem('uid');
    const recipeId = e.target.dataset.recipeId;
    if (!uid) {
      alert('Please login first so RecipeGenie can save your meal to dashboard and health tracker.');
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
          <h3 style="margin-bottom:0.6rem;">Meal saved to your tracker</h3>
          <p><strong>Status:</strong> ${payload.health_label || 'Moderate'}</p>
          <p><strong>Health score:</strong> ${payload.health_score || 0}/100</p>
          <p><strong>Calories:</strong> ${payload.nutrition?.calories || 0} kcal</p>
          <p><strong>Protein:</strong> ${payload.nutrition?.protein || 0} g</p>
          <p><strong>Fiber:</strong> ${payload.nutrition?.fiber || 0} g</p>
          <p><strong>Notes:</strong> ${(payload.nutrition_notes || []).join(', ') || 'Nutrition data saved'}</p>
          ${payload.notification ? `<p style="color:#c62828; margin-top:0.6rem;"><strong>Warning:</strong> ${payload.notification}</p>` : '<p style="margin-top:0.6rem; color:var(--secondary);"><strong>Good:</strong> Dashboard and health tracker updated successfully.</p>'}
        `;
      }

      if (recommendationBox) {
        if (Array.isArray(payload.recommendations) && payload.recommendations.length) {
          recommendationBox.style.display = 'block';
          recommendationBox.innerHTML = `
            <h3 style="margin-bottom:0.8rem;">Healthy recipes for your next meal</h3>
            ${payload.recommendations.map(recipe => `
              <p style="margin-bottom:0.6rem;">
                <a href="/recipe-detail/${recipe.recipe_id}"><strong>${recipe.name}</strong></a><br>
                <span style="color:var(--gray);">${recipe.reason}</span>
              </p>
            `).join('')}
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
    const uid = localStorage.getItem('uid');
    if (uid) {
      const res = await fetch(`/history/${uid}`);
      const hist = await res.json();
      const container = document.querySelector('.history-container') || document.getElementById('history-list');
      if (!container) return;

      container.innerHTML = '';

      if (!hist.length) {
        container.innerHTML = '<div class="history-empty">Cook a recipe to start building your cooking history.</div>';
        return;
      }

      hist.forEach(item => {
        const recipe = item.recipe || {};
        const healthType = recipe.health_label || recipe.category || 'Moderate';
        const div = document.createElement('div');
        div.classList.add('history-card');
        div.innerHTML = `
          <img src="${recipe.image_url || 'https://recipesimages.edgeone.app/default.jpg'}" alt="${recipe.name || 'Recipe'}" onerror="this.src='https://recipesimages.edgeone.app/default.jpg'">
          <div class="history-card-body">
            <div class="history-meta">
              <span>${item.date ? new Date(item.date).toLocaleDateString() : 'Recently cooked'}</span>
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

function createRecipeCard(recipe) {

  const card = document.createElement('div');
  card.classList.add('recipe-card');
  const hasMatchData = Array.isArray(recipe.matched_ingredients) || recipe.matching_score;
  const isLiked = recipe.isFavorite === true;
  const ingredients = Array.isArray(recipe.ingredients)
    ? recipe.ingredients
    : (typeof recipe.ingredients === "string" ? [recipe.ingredients] : []);
  const healthType = recipe.health_label || recipe.category || 'Moderate';

  card.innerHTML = `
    <div class="card-image-wrap">
      <img
        class="card-image"
        src="${recipe.image_url || 'https://recipesimages.edgeone.app/default.jpg'}"
        alt="${recipe.name}"
        onerror="this.src='https://recipesimages.edgeone.app/default.jpg'"
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

  // Prevent multiple calls
  if (isLoading || !hasMore) return;
  isLoading = true;

  // Get UI elements safely
  const loading = document.getElementById('loading');
  const noMore = document.getElementById('no-more');
  const grid = document.querySelector('.recipe-grid');

  // Show loading
  if (loading) loading.style.display = 'block';
  if (noMore) noMore.style.display = 'none';

  // Get filters
  const search = document.getElementById('search-input')?.value || '';
  const state = document.getElementById('state-select')?.value || 'All';
  const highRated = document.getElementById('high-rated')?.checked || false;

  // Build URL
  let url = `/get-recipes?state=${encodeURIComponent(state)}&search=${encodeURIComponent(search)}&high_rated=${highRated}&limit=50`;

  if (!reset && lastRecipeId) {
    url += `&last_doc_id=${encodeURIComponent(lastRecipeId)}`;
  }

  try {

    // ✅ FETCH API (IMPORTANT FIX)
    const res = await fetch(url);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();

    console.log("API DATA:", data);

    // Reset grid if needed
    if (reset && grid) {
      grid.innerHTML = '';
      lastRecipeId = null;
      hasMore = true;
    }

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
      grid.innerHTML = '<p style="text-align:center;">No recipes found</p>';
    } else if (!hasMore && noMore) {
      noMore.style.display = 'block';
    }

  } catch (err) {

    console.error('Error loading recipes:', err);

    if (grid) {
      grid.innerHTML += `
        <p style="color:red; text-align:center;">
          Error loading recipes. Please try again.
        </p>
      `;
    }

  } finally {

    isLoading = false;

    if (loading) loading.style.display = 'none';
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

    if (!input) {
        if (output) {
          output.innerHTML = '<div class="generated-empty"><h2>Add ingredients first</h2><p>Example: tomato, onion, paneer, rice</p></div>';
        }
        return;
    }

    const ingredients = input.split(",").map(i => i.trim()).filter(Boolean);
    output.innerHTML = '<div class="generated-empty"><h2>Generating your recipe...</h2><p>RecipeGenie is building steps and nutrition details.</p></div>';

    output.innerHTML = "⏳ Generating recipe...";

    try {
        output.innerHTML = '<div class="generated-empty"><h2>Generating your recipe...</h2><p>RecipeGenie is building steps and nutrition details.</p></div>';
        const res = await fetch('/generate-recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ingredients })
        });

        if (!res.ok) {
            throw new Error("Server error");
        }

        const data = await res.json();

        if (data.error) {
            output.innerHTML = "❌ " + data.error;
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
        output.innerHTML = "❌ Failed to connect to server";
    }
}

window.generateRecipe = generateRecipe;

document.getElementById('generate-recipe-form')?.addEventListener('submit', event => {
  event.preventDefault();
  generateRecipe();
});

async function loadHealthReport(){

const uid = localStorage.getItem("uid")

if(!uid) return

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
          <h3>${recipe.name}</h3>
          <p>${recipe.reason}</p>
          <a href="/recipe-detail/${recipe.recipe_id}" class="btn primary">Cook This</a>
        </div>
      `).join("")
    : '<div class="insight-item"><p>No healthy recommendations available yet.</p></div>'
}

const recentMealsGrid = document.getElementById("recent-meals-grid")
if (recentMealsGrid) {
  const meals = Array.isArray(data.recent_meals) ? data.recent_meals : []
  recentMealsGrid.innerHTML = meals.length
    ? meals.map(meal => `
        <div class="insight-item">
          <h3>${meal.recipe_name || "Recipe"}</h3>
          <p>${meal.health_label || "Moderate"}</p>
          <p>${meal.nutrition?.calories || 0} kcal</p>
          <p>${meal.cooked_at ? new Date(meal.cooked_at).toLocaleDateString() : ""}</p>
        </div>
      `).join("")
    : '<div class="insight-item"><p>No meals tracked yet. Cook a recipe to start monitoring.</p></div>'
}

}

async function loadDashboardReport() {

const uid = localStorage.getItem("uid")

if(!uid || !document.getElementById("dashboard-total-cooked")) return

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

}

console.log(document.getElementById("recipes-container"));
console.log(document.getElementById("favorites-container"));

// Load favorites
async function loadFavorites() {
  const uid = localStorage.getItem('uid');
  const favGrid = document.querySelector('.favorite-grid');
  if (!uid || !favGrid) return;

  try {
    const res = await fetch(`/favorites/${uid}`);
    if (!res.ok) throw new Error('Failed to load favorites');

    const favorites = await res.json();
    favGrid.innerHTML = favorites.length === 0 
      ? '<p style="text-align:center; padding:2rem;">You haven\'t liked any recipes yet.</p>'
      : '';

    favorites.forEach(fav => {
      fav.isFavorite = true;
      const card = createRecipeCard(fav);
      favGrid.appendChild(card);
    });
  } catch (err) {
    console.error('Favorites error:', err);
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

        const res = await fetch("/detect-ingredients", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        addDetectedIngredients(data.ingredients || [], "Camera");

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

    fetch("/detect-ingredients", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        addDetectedIngredients(data.ingredients || [], "Image");

    })
    .catch(err => console.error(err));
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
document.getElementById('state-select')?.addEventListener('change', () => loadRecipes(true));

// Like / Unlike handler
document.addEventListener('click', async e => {
  const btn = e.target.closest('.like-btn');
  if (!btn) return;

  const uid = localStorage.getItem('uid');
  if (!uid) {
    alert('Please login to like recipes');
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



