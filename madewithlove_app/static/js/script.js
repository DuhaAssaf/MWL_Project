document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("product-form");
  const tableBody = document.getElementById("product-table");
  const imageInput = document.getElementById("product-image");
  const previewImg = document.getElementById("image-preview");
  const paginationInfo = document.getElementById("pagination-info");
  const prevPageBtn = document.getElementById("prev-page");
  const nextPageBtn = document.getElementById("next-page");

  let products = [];
  let currentPage = 1;
  const itemsPerPage = 5;

  function showToast(msg, success = true, undoCallback = null) {
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${success ? 'success' : 'danger'} border-0 show position-fixed bottom-0 end-0 m-3`;
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${msg}</div>
        ${undoCallback ? '<button class="btn btn-link btn-sm text-white me-2 undo-btn">Undo</button>' : ''}
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>`;
    document.body.appendChild(toast);

    if (undoCallback) {
      toast.querySelector(".undo-btn").addEventListener("click", () => {
        undoCallback();
        toast.remove();
      });
    }

    setTimeout(() => toast.remove(), 5000);
  }

  function renderTable(data) {
    tableBody.innerHTML = "";
    data.forEach((p, index) => {
      const row = document.createElement("tr");
      row.setAttribute("data-id", p.id);
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
    const filtered = products;
    renderTable(filtered.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage));
    updatePagination(filtered.length);
  }

  function fetchProducts() {
    fetch("/dashboard/products/json/")
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          products = data.products;
          applyFilters();
        } else {
          showToast("Failed to load products", false);
        }
      })
      .catch(err => {
        console.error("Fetch error:", err);
        showToast("Error loading products", false);
      });
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
  
    if (!confirm(`Are you sure you want to delete "${product.name}"?`)) {
      return; // cancel deletion
    }
  
    const formData = new FormData();
    formData.append("product_id", product.id);
    formData.append("delete", "true");
  
    fetch("/dashboard/add-edit-product/", {
      method: "POST",
      body: formData,
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast("Product deleted", true, () => undoDelete(product.id));
          fetchProducts();
        } else {
          showToast(data.message || "Error deleting product", false);
        }
      })
      .catch(() => showToast("Delete failed", false));
  };
  
  function undoDelete(productId) {
    const formData = new FormData();
    formData.append("product_id", productId);
    formData.append("undo", "true");

    fetch("/dashboard/add-edit-product/", {
      method: "POST",
      body: formData,
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast("Undo successful");
          fetchProducts();
        } else {
          showToast("Undo failed", false);
        }
      })
      .catch(() => showToast("Undo error", false));
  }

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
        fetchProducts();
      } else {
        showToast(data.message || "Error saving product", false);
      }
    })
    .catch(error => {
      console.error("Save error:", error);
      showToast("Something went wrong", false);
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

  fetchProducts();
});

// explore page functionallity
function openOrderModal(id, name, price, stock) {
  document.getElementById("orderProductId").value = id;
  document.getElementById("orderProductName").textContent = `${name} - $${price}`;
  const quantityInput = document.getElementById("orderQuantity");
  quantityInput.max = stock;
  quantityInput.value = 1;
  const modal = new bootstrap.Modal(document.getElementById("orderModal"));
  modal.show();
}

document.getElementById("orderForm")?.addEventListener("submit", function (e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);

  fetch("/cart/add/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
    },
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast("Product added to cart!");
        bootstrap.Modal.getInstance(document.getElementById("orderModal")).hide();
      } else {
        showToast(data.message || "Failed to add to cart", false);
      }
    })
    .catch(() => {
      showToast("Something went wrong", false);
    });
});

