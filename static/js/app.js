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


// upload imagee

// function uploadImage(){

//     const input = document.getElementById("imageInput")
//     const file = input.files[0]

//     if(!file){
//         alert("Select an image first")
//         return
//     }

//     const preview = document.getElementById("preview")
//     preview.src = URL.createObjectURL(file)

//     const formData = new FormData()
//     formData.append("image", file)

//     fetch("/detect",{
//         method:"POST",
//         body:formData
//     })
//     .then(res=>res.json())
//     .then(data=>{

//         const resultDiv = document.getElementById("results")

//         resultDiv.innerHTML = ""

//         if(data.detected_ingredients.length === 0){
//             resultDiv.innerHTML = "No ingredients detected"
//             return
//         }

//         data.detected_ingredients.forEach(item=>{
//             const p = document.createElement("p")
//             p.innerText = item.ingredient + " (" + item.confidence + ")"
//             resultDiv.appendChild(p)
//         })

//     })
// }
// Gujarat Smart Recipe Recommendation System - JavaScript

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
const addBtn = document.getElementById('add-ingredient');
const findBtn = document.getElementById('find-recipes');

function addTag(text = ingredientInput.value.trim()) {
  if (!text) return;
  const tag = document.createElement('span');
  tag.classList.add('tag');
  tag.innerHTML = `${text} <i class="fas fa-times"></i>`;
  tag.querySelector('i').addEventListener('click', () => tag.remove());
  tagsContainer.appendChild(tag);
  ingredientInput.value = '';
}

if (addBtn) addBtn.addEventListener('click', () => addTag());
if (ingredientInput) ingredientInput.addEventListener('keypress', e => { if (e.key === 'Enter') addTag(); });

// Voice Input
const micBtn = document.querySelector('.mic');
if (micBtn) {
  micBtn.addEventListener('click', () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.onresult = e => addTag(e.results[0][0].transcript);
    recognition.start();
  });
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

    // Collect ingredients from tags
    const ingredients = Array.from(tagsContainer.querySelectorAll('.tag'))
      .map(tag => tag.textContent.replace('×','').trim());

    console.log("Finding recipes with ingredients:", ingredients);

    if (ingredients.length === 0) {
      alert("Please add ingredients first");
      return;
    }

    document.querySelector('.loading').style.display = 'block';

    const formData = new FormData();
    formData.append('ingredients', ingredients.join(' '));

    if (imageInput.files[0]) {
      formData.append('image', imageInput.files[0]);
    }

    const uid = localStorage.getItem('uid');
    if (uid) {
      formData.append('user_id', uid);
    }

    try {

      const res = await fetch('/recommend', {
        method: 'POST',
        body: formData
      });

      const recs = await res.json();

      console.log("Recipes received:", recs);

      const grid = document.querySelector('.recipe-grid');
      grid.innerHTML = '';

      recs.forEach(recipe => {

        const card = createRecipeCard(recipe);
        grid.appendChild(card);

        if (recipe.status === 'show_missing') {

          const modal = document.createElement('div');

          modal.style.position = 'fixed';
          modal.style.top = '50%';
          modal.style.left = '50%';
          modal.style.transform = 'translate(-50%, -50%)';
          modal.style.background = 'white';
          modal.style.padding = '20px';
          modal.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';

          modal.innerHTML = `
            Missing ingredients: ${recipe.missing.join(', ')}
            <br><br>
            <button onclick="this.parentNode.remove()">Close</button>
          `;

          document.body.appendChild(modal);
        }

      });

    } catch (error) {
      console.error("Recommendation error:", error);
    }

    document.querySelector('.loading').style.display = 'none';

  });
}
// function createRecipeCard(recipe) {
//   const card = document.createElement('div');
//   card.classList.add('recipe-card');
//   card.innerHTML = `
//     <img src="/static/images/${recipe.name_of_Dish}.jpg" alt="${recipe.name_of_Dish}" onerror="this.src='placeholder.jpg'">
//     <h3>${recipe.name_of_Dish}</h3>
//     <span class="badge ${recipe.category.toLowerCase().replace(' ', '-')}">${recipe.category}</span>
//     <div class="match-bar"><div class="progress" style="width: ${recipe.matching_score}%;"></div></div>
//     <span class="match-text">${recipe.matching_score}% Match</span>
//     <div class="buttons">
//       <button class="btn primary cooked-btn" data-recipe-id="${recipe.recipe_id}">Cook This</button>
//       <a href="/recipe?id=${recipe.recipe_id}" class="btn primary">View Full Recipe</a>
//     </div>
//   `;
//   return card;
// }

// Cooked buttons
document.addEventListener('click', async e => {
  if (e.target.classList.contains('cooked-btn')) {
    const uid = localStorage.getItem('uid');
    const recipeId = e.target.dataset.recipeId;
    if (uid && recipeId) {
      await fetch('/cooked', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: uid, recipe_id: recipeId })
      });
      location.reload();
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
      const container = document.querySelector('.history-container') || document.createElement('div');
      container.classList.add('history-container');
      container.innerHTML = '';
      hist.forEach(item => {
        const div = document.createElement('div');
        div.classList.add('history-item');
        div.innerHTML = `
          <h3>${item.recipe.name}</h3>
          <p>Date: ${new Date(item.date).toLocaleDateString()}</p>
          <span class="badge ${item.recipe.category.toLowerCase()}">${item.recipe.category}</span>
          <button class="btn primary cooked-btn" data-recipe-id="${item.recipe_id}">Cook Again</button>
        `;
        container.appendChild(div);
      });
      document.querySelector('.section').appendChild(container);
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

// Create a single recipe card
function createRecipeCard(recipe) {
  const card = document.createElement('div');
  // const imgpath = https://recipe-images.edgeone.app/Kesar_Peda_Recipe_14_400x320.jpg
  //  <img src="/static/images/${recipe.name.replace(/ /g, '_')}.jpg" alt="${recipe.name}" 
  //        onerror="this.src='https://via.placeholder.com/300x180?text=${encodeURIComponent(recipe.name)}'"></img>
  card.classList.add('recipe-card');
  card.innerHTML = `
    <img src="${recipe.image_url}" alt="${recipe.name}" 
         onerror="this.src='https://recipesimages.edgeone.app/default.jpg?text=${encodeURIComponent(recipe.name)}'">
    <h3>${recipe.name}</h3>
    <span class="badge ${recipe.category?.toLowerCase() || 'moderate'}">${recipe.category || 'Moderate'}</span>
    <p>Rating: ${recipe.ratings || 'N/A'}</p>
    <div class="buttons">
      <button class="like-btn ${recipe.isFavorite ? 'liked' : ''}" data-recipe-id="${recipe.recipe_id}">
        <i class="fas fa-heart"></i> ${recipe.isFavorite ? 'Liked' : 'Like'}
      </button>
      <a href="/recipe-detail/${recipe.recipe_id}" class="btn primary">Cook This</a>
    </div>
  `;
  return card;
}

// Load recipes with pagination
async function loadRecipes(reset = false) {
  if (isLoading || !hasMore) return;
  isLoading = true;

  const loading = document.getElementById('loading');
  const noMore = document.getElementById('no-more');
  loading.style.display = 'block';
  noMore.style.display = 'none';

  const search = document.getElementById('search-input')?.value || '';
  const state = document.getElementById('state-select')?.value || 'All';
  const highRated = document.getElementById('high-rated')?.checked || false;

  let url = `/get-recipes?state=${encodeURIComponent(state)}&search=${encodeURIComponent(search)}&high_rated=${highRated}&limit=50`;
  if (!reset && lastRecipeId) {
    url += `&last_doc_id=${encodeURIComponent(lastRecipeId)}`;
  }

 
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();

    console.log("Received from /get-recipes:", data);

    const grid = document.querySelector('.recipe-grid');

    if (reset) {
      grid.innerHTML = '';
      lastRecipeId = null;
      hasMore = true;
    }

    data.recipes.forEach(recipe => {
      grid.appendChild(createRecipeCard(recipe));
    });

    lastRecipeId = data.last_doc_id;
    hasMore = data.has_more === true;

    if (!hasMore && grid.children.length === 0) {
      grid.innerHTML = '<p style="text-align:center; padding:3rem;">No recipes found matching your criteria.</p>';
    } else if (!hasMore) {
      noMore.style.display = 'block';
    }

  } catch (err) {
    console.error('Error loading recipes:', err);
    document.querySelector('.recipe-grid').innerHTML += '<p style="color:red; text-align:center;">Error loading recipes. Please try again.</p>';
  } finally {
    isLoading = false;
    loading.style.display = 'none';
  }
}

async function loadHealthReport(){

const uid = localStorage.getItem("uid")

if(!uid) return

const res = await fetch(`/health-report/${uid}`)

const data = await res.json()

document.getElementById("healthy-count").innerText = data.healthy
document.getElementById("moderate-count").innerText = data.moderate
document.getElementById("fast-count").innerText = data.fastfood

document.getElementById("health-score").innerText =
`Health Score: ${data.health_score} (${data.status})`

document.getElementById("health-progress").style.width =
Math.min(100,Math.max(0,data.health_score*5))+"%"

}

// Load favorites
async function loadFavorites() {
  const uid = localStorage.getItem('uid');
  if (!uid) return;

  try {
    const res = await fetch(`/favorites/${uid}`);
    if (!res.ok) throw new Error('Failed to load favorites');

    const favorites = await res.json();
    const favGrid = document.querySelector('.favorite-grid');
    favGrid.innerHTML = favorites.length === 0 
      ? '<p style="text-align:center; padding:2rem;">You haven\'t liked any recipes yet.</p>'
      : '';

    favorites.forEach(fav => {
      const card = createRecipeCard(fav.recipe);
      card.querySelector('.like-btn').classList.add('liked');
      card.querySelector('.like-btn').textContent = 'Liked';
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

function detectIngredients() {

    const imageUpload = document.getElementById("imageUpload");
    const resultsDiv = document.getElementById("detected-results");

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
    .then(response => response.json())
    .then(data => {

        resultsDiv.innerHTML = "";

        if (!data.ingredients || data.ingredients.length === 0) {
            resultsDiv.innerHTML = "No ingredients detected";
            return;
        }

        data.ingredients.forEach(item => {

            const p = document.createElement("p");
            p.innerText = item.ingredient + " (" + item.confidence.toFixed(2) + ")";

            resultsDiv.appendChild(p);

        });

    })
    .catch(error => {
        console.error("Error:", error);
    });

}

window.detectIngredients = detectIngredients;

const startCameraBtn = document.getElementById("startCamera");
const captureBtn = document.getElementById("captureBtn");
const detectBtn = document.getElementById("detectBtn");

const video = document.getElementById("camera");
const canvas = document.getElementById("canvas");

const imageUpload = document.getElementById("imageUpload");
const resultsDiv = document.getElementById("detected-results");

let stream;


/* -------------------------
START CAMERA
--------------------------*/

startCameraBtn.addEventListener("click", async () => {

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });

        video.srcObject = stream;

        video.style.display = "block";
        captureBtn.style.display = "inline-block";

    } catch (err) {

        alert("Camera access denied");

    }

});



/* -------------------------
CAPTURE IMAGE
--------------------------*/

captureBtn.addEventListener("click", async () => {

    const ctx = canvas.getContext("2d");

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

        displayResults(data.ingredients);

    });

});



/* -------------------------
UPLOAD IMAGE
--------------------------*/

detectBtn.addEventListener("click", async () => {

    if (imageUpload.files.length === 0) {
        alert("Please select image");
        return;
    }else{
      const formData = new FormData();
      formData.append("image", imageUpload.files[0]);

      const res = await fetch("/detect-ingredients", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      displayResults(data.ingredients);
    }

    

});



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
window.addEventListener('scroll', () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
    loadRecipes(); // load next page
  }
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
  
    loadRecipes(true);
    loadFavorites();

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



