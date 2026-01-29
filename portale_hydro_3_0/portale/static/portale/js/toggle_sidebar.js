document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("toggle-sidebar");
  if (!button) {
    return;
  }

  const updateButton = () => {
    const isExpanded = !document.body.classList.contains("sidebar-collapsed");
    button.setAttribute("aria-expanded", String(isExpanded));
    button.textContent = isExpanded ? "Nascondi lista" : "Mostra lista";
  };

  button.addEventListener("click", () => {
    document.body.classList.toggle("sidebar-collapsed");
    updateButton();
  });

  updateButton();
});
