document.addEventListener("DOMContentLoaded", async () => {
  const gallery = document.getElementById("gallery");

  try {
    const res = await fetch("assets/kittens.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to load kittens.json: ${res.status}`);
    const items = await res.json();

    items.forEach(item => {
      const card = document.createElement("figure");
      card.className = "card";

      let mediaEl;
      if (item.type === "video") {
        mediaEl = document.createElement("video");
        mediaEl.src = item.src;
        mediaEl.controls = true;
        mediaEl.preload = "metadata";
        mediaEl.playsInline = true;
        mediaEl.className = "media";
        if (item.poster) mediaEl.setAttribute("poster", item.poster);
      } else {
        mediaEl = document.createElement("img");
        mediaEl.src = item.src;
        mediaEl.loading = "lazy";
        mediaEl.decoding = "async";
        mediaEl.alt = item.alt || item.title || "Kitten photo";
        mediaEl.className = "media";
      }

      const caption = document.createElement("figcaption");
      caption.className = "caption";
      caption.textContent = item.title || "";

      card.appendChild(mediaEl);
      card.appendChild(caption);
      gallery.appendChild(card);
    });
  } catch (err) {
    console.error(err);
    gallery.innerHTML = `<p style="color:#b00020">Could not load gallery. Check <code>assets/kittens.json</code> and your file links.</p>`;
  }
});
