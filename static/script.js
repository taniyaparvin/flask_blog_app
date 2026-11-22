const search = document.getElementById("search");
if (search) {
  search.addEventListener("input", () => {
    const term = search.value.toLowerCase();
    document.querySelectorAll(".post-card").forEach((card) => {
      card.style.display = card.textContent.toLowerCase().includes(term) ? "" : "none";
    });
  });
}

document.querySelectorAll(".confirm-delete").forEach((form) => {
  form.addEventListener("submit", (e) => {
    if (!confirm("Delete this post? This cannot be undone.")) e.preventDefault();
  });
});
