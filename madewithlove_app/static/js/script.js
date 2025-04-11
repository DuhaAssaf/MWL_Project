// Updated script.js with Register/Login Validation + AJAX Product CRUD + Toasts + Pagination + Filters + Image Preview

document.addEventListener("DOMContentLoaded", function () {
  // ✅ Register/Login form validation
  const registerForm = document.querySelector("form[action='/register/']");
  const loginForm = document.querySelector("form[action='/login/']");

  if (registerForm) {
    const password1 = registerForm.querySelector("input[name='password1']");
    const password2 = registerForm.querySelector("input[name='password2']");
    const email = registerForm.querySelector("input[name='email']");
    const phone = registerForm.querySelector("input[name='phone_number']");

    registerForm.addEventListener("submit", function (e) {
      let valid = true;
      let messages = [];

      if (password1.value.length < 8) messages.push("Password must be at least 8 characters long.");
      if (password1.value !== password2.value) messages.push("Passwords do not match.");
      if (!/^\S+@\S+\.\S+$/.test(email.value)) messages.push("Invalid email address.");
      if (phone && phone.value && !/^\+?[0-9]{7,15}$/.test(phone.value)) messages.push("Invalid phone number format.");

      if (messages.length) {
        e.preventDefault();
        alert(messages.join("\n"));
      }
    });
  }

  if (loginForm) {
    const username = loginForm.querySelector("input[name='username']");
    const password = loginForm.querySelector("input[name='password']");

    loginForm.addEventListener("submit", function (e) {
      let messages = [];
      if (!username.value || username.value.length < 3) messages.push("Enter a valid username or email.");
      if (!password.value || password.value.length < 6) messages.push("Password must be at least 6 characters.");

      if (messages.length) {
        e.preventDefault();
        alert(messages.join("\n"));
      }
    });
  }

  // ✅ Product Dashboard Management
  const form = document.getElementById("product-form");
  const tableBody = document.getElementById("product-table");
  const searchBar = document.getElementById("search-bar");
  const categoryFilter = document.getElementById("category-filter");
  const imageInput = document.getElementById("product-image");
  const previewImg = document.getElementById("image-preview");
  const paginationInfo = document.getElementById("pagination-info");
  const prevPageBtn = document.getElementById("prev-page");
  const nextPageBtn = document.getElementById("next-page");

  if (!form || !tableBody) return;

  let products = [];
  let currentPage = 1;
  const itemsPerPage = 5;

  function showToast(msg, success = true) {
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${success ? 'success' : 'danger'} border-0 show position-fixed bottom-0 end-0 m-3`;
    toast.innerHTML = `<div class="d-flex"><div class="toast-body">${msg}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  function renderTable(data) {
    tableBody.innerHTML = "";
    data.forEach((p, index) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><img src="${p.image}" width="50" class="img-fluid rounded" /></td>
        <td>${p.name}</td>
        <td>${p.category}</td>
        <td>$${p.price}</td>
        <td>${p.description}</td>
        <td>
          <div class="d-flex justify-content-center">
            <button class="btn btn-sm btn-warning me-2" onclick="editProduct(${index})" data-bs-toggle="modal" data-bs-target="#productModal">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="deleteProduct(${index})">Delete</button>
          </div>
        </td>`;
      tableBody.appendChild(row);
    });
  }

  function updatePagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    paginationInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage >= totalPages;
  }

  function applyFilters() {
    const term = searchBar.value.toLowerCase();
    const cat = categoryFilter.value;
    const filtered = products.filter(p => {
      const matchText = p.name.toLowerCase().includes(term) || p.category.toLowerCase().includes(term) || p.description.toLowerCase().includes(term);
      const matchCat = !cat || p.category === cat;
      return matchText && matchCat;
    });
    renderTable(filtered.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage));
    updatePagination(filtered.length);
  }

  function updateCategoryDropdown() {
    const categories = [...new Set(products.map(p => p.category))];
    categoryFilter.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(cat => {
      const option = document.createElement("option");
      option.value = cat;
      option.textContent = cat;
      categoryFilter.appendChild(option);
    });
  }

  window.editProduct = index => {
    const p = products[index];
    form["product-name"].value = p.name;
    form["product-category"].value = p.category;
    form["product-price"].value = p.price;
    form["product-image"].value = p.image;
    form["product-description"].value = p.description;
    previewImg.src = p.image;
    previewImg.style.display = p.image ? "block" : "none";
  };

  window.deleteProduct = index => {
    if (confirm(`Delete "${products[index].name}"?`)) {
      products.splice(index, 1);
      applyFilters();
      updateCategoryDropdown();
      showToast("Product deleted successfully.");
    }
  };

  form.onsubmit = e => {
    e.preventDefault();
    const newProduct = {
      name: form["product-name"].value.trim(),
      category: form["product-category"].value.trim(),
      price: form["product-price"].value.trim(),
      image: form["product-image"].value.trim() || "https://via.placeholder.com/50",
      description: form["product-description"].value.trim()
    };
    products.push(newProduct);
    updateCategoryDropdown();
    currentPage = 1;
    applyFilters();
    bootstrap.Modal.getInstance(document.getElementById("productModal")).hide();
    form.reset();
    previewImg.style.display = "none";
    showToast("Product saved successfully.");
  };

  imageInput.addEventListener("input", () => {
    const url = imageInput.value;
    previewImg.src = url;
    previewImg.style.display = url ? "block" : "none";
  });

  prevPageBtn.addEventListener("click", () => {
    if (currentPage > 1) currentPage--;
    applyFilters();
  });

  nextPageBtn.addEventListener("click", () => {
    const totalPages = Math.ceil(products.length / itemsPerPage);
    if (currentPage < totalPages) currentPage++;
    applyFilters();
  });

  searchBar.addEventListener("input", () => {
    currentPage = 1;
    applyFilters();
  });

  categoryFilter.addEventListener("change", () => {
    currentPage = 1;
    applyFilters();
  });

  function extractInitialProducts() {
    products = [];
    document.querySelectorAll("#product-table tr").forEach(row => {
      const cols = row.querySelectorAll("td");
      if (cols.length < 5) return;
      const image = cols[0].querySelector("img")?.src || "";
      const name = cols[1].textContent.trim();
      const category = cols[2].textContent.trim();
      const price = cols[3].textContent.replace("$", "").trim();
      const description = cols[4].textContent.trim();
      products.push({ name, category, price, image, description });
    });
  }

  extractInitialProducts();
  updateCategoryDropdown();
  applyFilters();
});