document.addEventListener("DOMContentLoaded", function () {
  // ✅ Register/Login Form Validation
  const registerForm = document.querySelector("form[action='/register/']");
  const loginForm = document.querySelector("form[action='/login/']");

  if (registerForm) {
    const password1 = registerForm.querySelector("input[name='password1']");
    const password2 = registerForm.querySelector("input[name='password2']");
    const email = registerForm.querySelector("input[name='email']");
    const phone = registerForm.querySelector("input[name='phone_number']");

    registerForm.addEventListener("submit", function (e) {
      let messages = [];
      if (password1.value.length < 8) messages.push("Password must be at least 8 characters.");
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
      row.setAttribute("data-id", p.id);  // ← this line is missing!
      row.innerHTML = `
        <td><img src="${p.image}" width="50" class="img-fluid rounded" /></td>
        <td>${p.name}</td>
        <td>${p.category}</td>
        <td>$${p.price}</td>
        <td>${p.stock}</td>
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
    const term = searchBar?.value.toLowerCase() || "";
    const filtered = products.filter(p =>
      p.name.toLowerCase().includes(term) ||
      p.description.toLowerCase().includes(term)
    );
    renderTable(filtered.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage));
    updatePagination(filtered.length);
  }

  window.editProduct = index => {
    const p = products[index];
    form["edit-product-id"].value = p.id;
    form["product-name"].value = p.name;
    form["product-price"].value = p.price;
    form["product-stock"].value = p.stock;
    form["product-description"].value = p.description;
    previewImg.src = p.image;
    previewImg.style.display = p.image ? "block" : "none";
  };

  window.deleteProduct = index => {
    const product = products[index];
    if (!product.id) {
      console.error("Missing product ID");
      showToast("Missing product ID", false);
      return;
    }

    if (confirm(`Delete "${product.name}"?`)) {
      console.log("Deleting product:", product.id);
      const formData = new FormData();
      formData.append("product_id", product.id);
      formData.append("delete", "true");

      console.log("🧪 Sending DELETE for product_id:", product.id); // for debugging


      fetch("/dashboard/add-edit-product/", {
        method: "POST",
        body: formData,
      })
      
      .then(res => res.json())
      .then(data => {
        console.log("🧪 DELETE response:", data);
        if (data.success) {
          showToast("Product deleted");
          window.location.reload();
        } else {
          showToast(data.message || "Error deleting product", false);
        }
      })
      .catch(() => showToast("Delete failed", false));

    }
  };

  form.onsubmit = e => {
    e.preventDefault();
    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast("Product saved successfully.");
        form.reset();
        previewImg.style.display = "none";
        bootstrap.Modal.getInstance(document.getElementById("productModal")).hide();
        window.location.reload();  // Refresh table to reflect changes
      } else {
        showToast(data.message || "Error occurred.", false);
        console.error("Server error:", data);
      }
    })
    .catch(error => {
      console.error("Fetch error:", error);
      showToast("Something went wrong.", false);
    });
  };

  imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = e => {
        previewImg.src = e.target.result;
        previewImg.style.display = "block";
      };
      reader.readAsDataURL(file);
    }
  });

  prevPageBtn?.addEventListener("click", () => {
    if (currentPage > 1) currentPage--;
    applyFilters();
  });

  nextPageBtn?.addEventListener("click", () => {
    const totalPages = Math.ceil(products.length / itemsPerPage);
    if (currentPage < totalPages) currentPage++;
    applyFilters();
  });

  searchBar?.addEventListener("input", () => {
    currentPage = 1;
    applyFilters();
  });

  function extractInitialProducts() {
    products = [];
    document.querySelectorAll("#product-table tr").forEach(row => {
      const id = row.getAttribute("data-id");
      const cols = row.querySelectorAll("td");
      if (cols.length < 5) return;
      const image = cols[0].querySelector("img")?.src || "";
      const name = cols[1].textContent.trim();
      const category = cols[2].textContent.trim();
      const price = cols[3].textContent.replace("$", "").trim();
      const stock = cols[4].textContent.trim();
      const description = cols[4].textContent.trim();
      products.push({ id, name, category, price, stock, image, description });
    });
  }

  extractInitialProducts();
  applyFilters();

  // ✅ Profile Page Form Validation + Image Preview
  const profileForm = document.getElementById("profileForm");
  if (profileForm) {
    profileForm.addEventListener("submit", function (e) {
      const storeName = this.store_name.value.trim();
      const description = this.description.value.trim();
      if (storeName.length < 6) {
        alert("Store name must be more than 5 characters.");
        e.preventDefault();
      }
      if (description.length < 15) {
        alert("Description must be more than 15 characters.");
        e.preventDefault();
      }
    });
  }

  const profileInput = document.getElementById("profilePictureInput");
  const profilePreview = document.getElementById("profilePreview");
  const storeInput = document.getElementById("storeLogoInput");
  const storePreview = document.getElementById("storeLogoPreview");

  if (profileInput) {
    profileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          profilePreview.src = event.target.result;
          profilePreview.style.display = "block";
        };
        reader.readAsDataURL(file);
      }
    });
  }

  if (storeInput) {
    storeInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          storePreview.src = event.target.result;
          storePreview.style.display = "block";
        };
        reader.readAsDataURL(file);
      }
    });
  }
});
