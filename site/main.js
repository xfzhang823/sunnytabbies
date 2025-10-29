document.addEventListener("DOMContentLoaded", async () => {
  const res = await fetch("assets/kittens.json", { cache: "no-store" });
  const items = await res.json();
  const gallery = document.getElementById("gallery");

  // IntersectionObserver to lazy-attach video sources
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting && e.target.tagName === "VIDEO" && !e.target.dataset.boot) {
        attachVideoSources(e.target);
        e.target.dataset.boot = "1";
      }
    });
  }, { rootMargin: "200px" });

  // ---- render cards -------------------------------------------------------
  items.forEach(item => {
    const card = document.createElement("figure");
    card.className = "card";

    let mediaEl;
    let imgElForLightbox = null; // reference to grid <img> if present

    if (item.type === "image") {
      // ----- IMAGE PATH ----------------------------------------------------
      const picture = document.createElement("picture");

      // allow simple 'thumb'/'src' with optional 'full'
      const usesSimpleSrc = !!(item.src || item.thumb);
      const gridSrc = item.thumb || item.src;                 // small preview
      const lightboxSrc = item.full || item.src || gridSrc;   // bigger for click

      // original multi-rendition path (expects item.base and -800/-1600/-2400 files)
      if (!usesSimpleSrc && item.base) {
        const webp = document.createElement("source");
        webp.type = "image/webp";
        webp.srcset = [
          `${item.base}-800.webp 800w`,
          `${item.base}-1600.webp 1600w`,
          `${item.base}-2400.webp 2400w`
        ].join(", ");
        webp.sizes = "(max-width: 600px) 96vw, (max-width: 1200px) 48vw, 32vw";
        picture.appendChild(webp);
      }

      const img = document.createElement("img");
      img.className = "media";
      img.loading = "lazy";
      img.decoding = "async";
      img.fetchPriority = "low";

      if (usesSimpleSrc) {
        img.src = gridSrc;
        img.alt = item.alt || item.title || "Kitten photo";
        img.dataset.full = lightboxSrc; // stash for lightbox
      } else {
        // fallback jpg path with responsive candidates
        img.src = `${item.base}-800.jpg`;
        img.srcset = [
          `${item.base}-800.jpg 800w`,
          `${item.base}-1600.jpg 1600w`,
          `${item.base}-2400.jpg 2400w`
        ].join(", ");
        img.sizes = "(max-width: 600px) 96vw, (max-width: 1200px) 48vw, 32vw";
        img.alt = item.alt || item.title || "Kitten photo";
        img.dataset.full = `${item.base}-2400.jpg`;
      }

      picture.appendChild(img);
      mediaEl = picture;
      imgElForLightbox = img;

    } else {
      // ----- VIDEO PATH ----------------------------------------------------
      const v = document.createElement("video");
      v.className = "media";
      v.controls = true;
      v.playsInline = true;
      v.preload = "metadata";
      if (item.poster) v.poster = item.poster;

      // If you use your own files, keep a base and attach sources lazily
      if (item.base) {
        v.dataset.base = item.base;   // e.g., /assets/media/clip-01
        io.observe(v);
      } else if (item.src) {
        // If a direct .mp4 src is provided in JSON, attach now
        const s = document.createElement("source");
        s.src = item.src;
        s.type = "video/mp4";
        v.appendChild(s);
      }

      mediaEl = v;
    }

    // caption (optional)
    if (item.title) {
      const figcap = document.createElement("figcaption");
      figcap.className = "caption";
      figcap.textContent = item.title;
      card.appendChild(figcap);
    }

    // place media first in figure (before caption)
    card.insertBefore(mediaEl, card.firstChild);

    // click-to-zoom (images) / lightbox
    const clickTarget = mediaEl.querySelector?.("img") || mediaEl; // picture -> img
    clickTarget.addEventListener("click", (e) => {
      // prevent video controls click from bubbling if desired:
      // if (clickTarget.tagName === "VIDEO") return;
      openLightbox(item, imgElForLightbox || clickTarget);
      e.stopPropagation();
    });
    clickTarget.style.cursor = (item.type === "image") ? "zoom-in" : "pointer";

    gallery.appendChild(card);
  });

  // ---- helpers ------------------------------------------------------------
  function attachVideoSources(video) {
    const base = video.dataset.base;
    // attach from high -> low, browser picks best it can play
    [["1080"], ["720"], ["480"]].forEach(([w]) => {
      const s = document.createElement("source");
      s.src = `${base}-${w}.mp4`;
      s.type = "video/mp4";
      s.setAttribute("data-quality", `${w}p`);
      video.appendChild(s);
    });
  }

  // Lightbox overlay
  const lb = document.getElementById("lightbox");
  const lbClose = document.getElementById("lb-close");
  lb.addEventListener("click", e => { if (e.target === lb || e.target === lbClose) closeLightbox(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeLightbox(); });

  function openLightbox(item, el) {
    lb.classList.add("open");
    lb.innerHTML = '<button id="lb-close" aria-label="Close" style="position:absolute;top:12px;right:14px">✕</button>';
    lb.querySelector("#lb-close").addEventListener("click", closeLightbox);

    if (item.type === "image") {
      // Prefer the explicit full URL we stashed on the grid <img>, then item.full
      const fullUrl =
        (el && el.dataset && el.dataset.full) ||
        item.full ||
        (item.base ? `${item.base}-2400.jpg` : item.src);

      // Simple, reliable: just show the chosen URL at near-full width
      const img = document.createElement("img");
      img.alt = (el && el.alt) || item.alt || item.title || "";
      img.decoding = "async";
      img.loading = "eager";
      img.style.maxWidth = "95vw";
      img.style.maxHeight = "90vh";
      img.src = fullUrl;

      lb.appendChild(img);
    } else {
      const v = document.createElement("video");
      v.controls = true; v.autoplay = true; v.playsInline = true;
      v.style.maxWidth = "95vw";
      v.style.maxHeight = "90vh";

      if (item.base) {
        // attach multiple qualities
        [["1080"], ["720"], ["480"]].forEach(([w]) => {
          const s = document.createElement("source");
          s.src = `${item.base}-${w}.mp4`;
          s.type = "video/mp4";
          v.appendChild(s);
        });
      } else if (item.src) {
        const s = document.createElement("source");
        s.src = item.src;
        s.type = "video/mp4";
        v.appendChild(s);
      }

      if (item.poster) v.poster = item.poster;
      lb.appendChild(v);
    }
  }

  function closeLightbox(){ lb.classList.remove("open"); }
});
