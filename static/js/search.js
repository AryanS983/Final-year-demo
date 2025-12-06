document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("fund-search");
  const list = document.getElementById("suggestions");

  input.addEventListener("input", async () => {
    const q = input.value.trim();
    if (q.length < 2) { list.innerHTML = ""; return; }
    const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    list.innerHTML = "";
    data.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item[1]} (${item[0]})`;
      li.dataset.code = item[0];
      li.onclick = () => {
        input.value = item[0]; // fill code for backend
        list.innerHTML = "";
      };
      list.appendChild(li);
    });
  });
});
