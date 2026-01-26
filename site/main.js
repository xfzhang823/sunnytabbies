document.addEventListener("DOMContentLoaded", async () => {
  const res = await fetch("assets/kittens.json", { cache: "no-store" });
  const items = await res.json();

  // fetch aggregate adoption info and render banner/section
  const adoptRes = await fetch("assets/adoption.json", { cache: "no-store" });
  const adopt = await adoptRes.json();
  renderAdoptionSummary(adopt);

  // pointer-coarseness flag (used for mobile-vs-desktop UX)
  const IS_COARSE =
    window.matchMedia && window.matchMedia("(pointer: coarse)").matches;

  // stage containers (match your HTML)
  const stageContainers = {
    first_moves: document.getElementById("stage-first_moves"),
    each_other: document.getElementById("stage-each_other"),
    big_big_world: document.getElementById("stage-big_big_world"),
    ready_for_launch: document.getElementById("stage-ready_for_launch"),
  };

  function renderAdoptionSummary(adopt) {
    if (!adopt) return;
    const { litter, policies, contact } = adopt;

    // Get elements
    const banner = document.querySelector(".adopt-banner");
    const homePref = document.getElementById("home-preference"); // optional slot
    const rehoming = document.getElementById("rehoming-copy"); // optional slot
    const emailEl = document.getElementById("adopt-email");
    const prefaceEl = document.getElementById("adopt-preface");

    // Banner text (no available / reserved)
    const bannerText =
      `${litter.total} kittens • ${litter.boys} boys / ${litter.girls} girls • ` +
      `born ${litter.born_on} • ready ${litter.ready_window} • ${litter.location}`;

    if (banner) {
      banner.textContent = bannerText;
    }

    // Optional: split content into separate placeholders if you have them
    if (homePref) {
      const prefs = policies?.home_preferences || {};
      const outdoor = Array.isArray(prefs.outdoor_options)
        ? prefs.outdoor_options.join(" ")
        : "";
      homePref.innerHTML = `
        <strong>${prefs.ideal_environment || ""}</strong><br>
        ${outdoor}
      `;
    }

    if (rehoming) {
      rehoming.textContent = `We’re not breeders—just rehoming our family cat’s litter${
        policies?.sibling_adopting_together
          ? " (reduced fee for sibling pairs)."
          : "."
      }`;
    }

    // Contact link + preface
    if (emailEl && contact?.email) {
      emailEl.href = `mailto:${contact.email}?subject=${encodeURIComponent(
        "Sunny Tabbies adoption inquiry"
      )}`;
    }
    if (prefaceEl && contact?.preface) {
      prefaceEl.textContent = contact.preface;
    }
  }

  // --- helpers: youtube detection/ID extraction ---------------------------
  const YT_HOSTS = ["youtube.com", "youtu.be"];
  function isYouTubeUrl(url = "") {
    try {
      const u = new URL(url);
      return YT_HOSTS.some((h) => u.hostname.includes(h));
    } catch {
      return false;
    }
  }
  function getYouTubeIdFromUrl(url = "") {
    try {
      const u = new URL(url);
      if (u.hostname.includes("youtu.be")) return u.pathname.slice(1);
      if (u.searchParams.get("v")) return u.searchParams.get("v");
      const m = u.pathname.match(/\/embed\/([a-zA-Z0-9_-]+)/);
      return m ? m[1] : null;
    } catch {
      return null;
    }
  }
  function getYouTubeId(item) {
    return item.videoId || (item.src && getYouTubeIdFromUrl(item.src)) || null;
  }

  // IntersectionObserver to lazy-attach video sources (mp4 only)
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (
          e.isIntersecting &&
          e.target.tagName === "VIDEO" &&
          !e.target.dataset.boot
        ) {
          attachVideoSources(e.target);
          e.target.dataset.boot = "1";
        }
      });
    },
    { rootMargin: "200px" }
  );

  // --- small helper to add a corner "pop out" button ----------------------
  function addPopoutButton(containerEl, onClick) {
    // ensure container is positioned
    const style = containerEl.style;
    if (!/relative|absolute|fixed/.test(style.position))
      style.position = "relative";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.setAttribute("aria-label", "Open in popup");
    btn.style.position = "absolute";
    btn.style.top = "8px";
    btn.style.right = "8px";
    btn.style.width = "44px"; // larger touch target
    btn.style.height = "44px";
    btn.style.display = "grid";
    btn.style.placeItems = "center";
    btn.style.border = "0";
    btn.style.borderRadius = "10px";
    btn.style.background = "rgba(0,0,0,.55)";
    btn.style.color = "white";
    btn.style.cursor = "pointer";
    btn.style.fontSize = "18px";
    btn.style.lineHeight = "1";
    btn.style.boxShadow = "0 2px 10px rgba(0,0,0,.3)";
    btn.style.zIndex = "2";
    btn.style.userSelect = "none";
    btn.style.webkitTapHighlightColor = "transparent";
    btn.textContent = "⤢";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      onClick();
    });
    containerEl.appendChild(btn);
  }

  // ---- render cards -------------------------------------------------------
  items.forEach((item) => {
    const card = document.createElement("figure");
    card.className = "card";

    let mediaEl;
    let imgElForLightbox = null; // reference to grid <img> if present

    if (item.type === "image") {
      // ----- IMAGE PATH ----------------------------------------------------
      const picture = document.createElement("picture");

      const usesSimpleSrc = !!(item.src || item.thumb);
      const gridSrc = item.thumb || item.src; // small preview
      const lightboxSrc = item.full || item.src || gridSrc; // bigger for click

      if (!usesSimpleSrc && item.base) {
        const webp = document.createElement("source");
        webp.type = "image/webp";
        webp.srcset = [
          `${item.base}-800.webp 800w`,
          `${item.base}-1600.webp 1600w`,
          `${item.base}-2400.webp 2400w`,
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
        img.src = `${item.base}-800.jpg`;
        img.srcset = [
          `${item.base}-800.jpg 800w`,
          `${item.base}-1600.jpg 1600w`,
          `${item.base}-2400.jpg 2400w`,
        ].join(", ");
        img.sizes = "(max-width: 600px) 96vw, (max-width: 1200px) 48vw, 32vw";
        img.alt = item.alt || item.title || "Kitten photo";
        img.dataset.full = `${item.base}-2400.jpg`;
      }

      picture.appendChild(img);
      mediaEl = picture;
      imgElForLightbox = img;
    } else if (
      item.type === "youtube" ||
      (item.type === "video" && isYouTubeUrl(item.src))
    ) {
      // ----- YOUTUBE PATH ----------------------------------------------------
      const vid = getYouTubeId(item);
      if (!vid) {
        console.warn("YouTube item missing videoId/src", item);
        return;
      }

      const wrapper = document.createElement("div");
      wrapper.className = "video-wrapper";
      wrapper.style.position = "relative";
      wrapper.style.width = "100%";
      wrapper.style.aspectRatio = "16 / 9";
      wrapper.style.overflow = "hidden";
      wrapper.style.borderRadius = "10px";

      const thumb = document.createElement("img");
      thumb.src =
        item.poster || `https://img.youtube.com/vi/${vid}/hqdefault.jpg`;
      thumb.alt = item.alt || item.title || "YouTube video";
      thumb.className = "media";
      thumb.style.cursor = "pointer";
      thumb.style.objectFit = "cover";

      // play overlay
      const playBtn = document.createElement("div");
      playBtn.style.position = "absolute";
      playBtn.style.inset = "0";
      playBtn.style.display = "flex";
      playBtn.style.alignItems = "center";
      playBtn.style.justifyContent = "center";
      playBtn.style.pointerEvents = "none";
      playBtn.innerHTML = `
        <div style="width:68px;height:48px;background:rgba(0,0,0,.6);border-radius:10px;display:flex;align-items:center;justify-content:center">
          <div style="margin-left:4px;width:0;height:0;border-top:10px solid transparent;border-bottom:10px solid transparent;border-left:16px solid white"></div>
        </div>`;

      // inline iframe builder (desktop / precision pointers)
      const loadIframeInline = () => {
        const iframe = document.createElement("iframe");
        iframe.src = `https://www.youtube.com/embed/${vid}?autoplay=1&modestbranding=1&rel=0&playsinline=1`;
        iframe.title = item.title || "YouTube video";
        iframe.allow =
          "autoplay; encrypted-media; picture-in-picture; web-share";
        iframe.setAttribute("allowfullscreen", "");
        iframe.setAttribute("playsinline", "true");
        iframe.style.position = "absolute";
        iframe.style.top = "0";
        iframe.style.left = "0";
        iframe.style.width = "100%";
        iframe.style.height = "100%";
        // swap just the thumbnail (keeps iOS gesture chain intact)
        wrapper.replaceChild(iframe, thumb);
      };

      const onThumbTap = (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        if (IS_COARSE) {
          openLightbox({
            ...item,
            type: "youtube",
            src: item.src,
            videoId: vid,
          });
        } else {
          loadIframeInline();
        }
      };

      // hook up both events (not passive, since we call preventDefault)
      thumb.addEventListener("pointerup", onThumbTap);
      thumb.addEventListener("click", onThumbTap);

      // assemble
      wrapper.appendChild(thumb);
      wrapper.appendChild(playBtn);
      addPopoutButton(wrapper, () =>
        openLightbox({ ...item, type: "youtube", src: item.src, videoId: vid })
      );
      mediaEl = wrapper;
    } else if (item.type === "video") {
      // ----- MP4 VIDEO PATH --------------------------------------------------
      const videoWrap = document.createElement("div");
      videoWrap.style.position = "relative";
      videoWrap.style.width = "100%";

      const v = document.createElement("video");
      v.className = "media";
      v.controls = true;
      v.playsInline = true;
      v.preload = "metadata";
      if (item.poster) v.poster = item.poster;

      if (item.base) {
        v.dataset.base = item.base; // e.g., /assets/media/clip-01
        io.observe(v);
      } else if (item.src) {
        const s = document.createElement("source");
        s.src = item.src;
        s.type = "video/mp4";
        v.appendChild(s);
      }

      videoWrap.appendChild(v);
      // pop-out button opens the same item in lightbox
      addPopoutButton(videoWrap, () => openLightbox(item, v));
      mediaEl = videoWrap;
    } else {
      console.warn("Unknown item.type, skipping:", item);
      return;
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

    // click-to-zoom / lightbox:
    // - Images: click anywhere on the tile opens lightbox
    if (item.type === "image") {
      const clickTarget = mediaEl.querySelector?.("img") || mediaEl;
      clickTarget.style.cursor = "zoom-in";
      clickTarget.addEventListener("click", (e) => {
        openLightbox(item, imgElForLightbox || clickTarget);
        e.stopPropagation();
      });
    }
    // - Videos/YouTube: play inline by default; use the corner ⤢ button for popup

    // Append to the correct stage container using the JSON `stage` field
    const stageKey = item.stage || "ready_for_launch";
    const container =
      stageContainers[stageKey] || stageContainers.ready_for_launch;

    if (container) {
      container.appendChild(card);
    } else {
      console.warn("No container found for stage:", stageKey, item);
    }
  });

  // ---- build stage jump nav (AFTER cards/stages are on page) -------------
  buildStageNav();

  // ---- helpers ------------------------------------------------------------
  function attachVideoSources(video) {
    const base = video.dataset.base;
    ["1080", "720", "480"].forEach((w) => {
      const s = document.createElement("source");
      s.src = `${base}-${w}.mp4`;
      s.type = "video/mp4";
      s.setAttribute("data-quality", `${w}p`);
      video.appendChild(s);
    });
  }

  // Lightbox overlay
  const lb = document.getElementById("lightbox");
  lb.addEventListener("click", (e) => {
    // close if clicking backdrop or the close button (which is recreated dynamically)
    if (e.target === lb || e.target?.id === "lb-close") closeLightbox();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeLightbox();
  });

  function renderLightboxText(item) {
    if (!item.story && !item.title) return null;

    const wrap = document.createElement("div");
    wrap.className = "lightbox-text";

    if (item.title) {
      const h3 = document.createElement("h3");
      h3.textContent = item.title;
      wrap.appendChild(h3);
    }

    if (item.story) {
      const p = document.createElement("p");
      p.textContent = item.story;
      wrap.appendChild(p);
    }

    return wrap;
  }

  function openLightbox(item, el) {
    lb.classList.add("open");
    lb.innerHTML =
      '<button id="lb-close" aria-label="Close" style="position:absolute;top:12px;right:14px">✕</button>';
    lb.querySelector("#lb-close").addEventListener("click", closeLightbox);

    if (item.type === "image") {
      const fullUrl =
        (el && el.dataset && el.dataset.full) ||
        item.full ||
        (item.base ? `${item.base}-2400.jpg` : item.src);

      const img = document.createElement("img");
      img.alt = (el && el.alt) || item.alt || item.title || "";
      img.decoding = "async";
      img.loading = "eager";
      img.style.maxWidth = "95vw";
      img.style.maxHeight = "90vh";
      img.src = fullUrl;
      lb.appendChild(img);
    } else if (item.type === "youtube" || isYouTubeUrl(item.src)) {
      const vid = getYouTubeId(item);
      const iframe = document.createElement("iframe");
      iframe.src = `https://www.youtube.com/embed/${vid}?autoplay=1&modestbranding=1&rel=0&playsinline=1`;
      iframe.title = item.title || "YouTube video";
      iframe.allow =
        "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      iframe.setAttribute("allowfullscreen", "");
      iframe.setAttribute("playsinline", "true"); // important for iOS inline
      Object.assign(iframe.style, {
        width: "95vw",
        maxWidth: "1200px",
        height: "calc(95vw * 9 / 16)",
        maxHeight: "90vh",
      });
      lb.appendChild(iframe);
    } else {
      const v = document.createElement("video");
      v.controls = true;
      v.autoplay = true;
      v.playsInline = true;
      v.style.maxWidth = "95vw";
      v.style.maxHeight = "90vh";

      if (item.base) {
        ["1080", "720", "480"].forEach((w) => {
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

    // ✅ ADD story if exists
    const textBlock = renderLightboxText(item);
    if (textBlock) {
      lb.appendChild(textBlock);
    }
  }

  function closeLightbox() {
    lb.classList.remove("open");
    lb.innerHTML = ""; // optional: ensures iframe/video stops
  }
});

// -------------------------------------------------------------------------
// Stage jump nav (YouTube-style horizontal tabs)
// -------------------------------------------------------------------------
function buildStageNav() {
  const mount = document.getElementById("stage-nav-inner");
  if (!mount) return;

  const navSections = Array.from(
    document.querySelectorAll(
      "section.gallery-stage[data-stage], section[data-stage-nav]"
    )
  );
  if (!navSections.length) return;

  const nav = document.createElement("div");
  nav.className = "stage-nav";
  nav.setAttribute("role", "tablist");
  nav.setAttribute("aria-label", "Jump to stage");

  navSections.forEach((sec) => {
    const stageKey = (sec.getAttribute("data-stage") || "").trim();
    const customLabel = (sec.getAttribute("data-stage-nav") || "").trim();
    if (!stageKey && !customLabel && !sec.querySelector("h2")) return;

    // ✅ Use the existing, unique grid id from your HTML: stage-first_moves, etc.
    const gridId = stageKey ? `stage-${stageKey}` : "";
    const gridEl = gridId ? document.getElementById(gridId) : null;

    // If the grid isn't found for some reason, fall back to the section itself
    const targetEl = gridEl || sec;

    const h2 = sec.querySelector("h2");
    const label = (customLabel || h2?.textContent || stageKey || "Stage").trim();

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "stage-tab";
    btn.textContent = label;
    btn.dataset.target = targetEl.id || ""; // might be empty if section has no id
    btn.setAttribute("role", "tab");

    btn.addEventListener("click", () => {
      // Prefer scrolling the *section* so the header is visible
      const toScroll =
        (gridEl && gridEl.closest("section.gallery-stage")) || sec;

      toScroll.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    nav.appendChild(btn);
  });

  mount.innerHTML = "";
  mount.appendChild(nav);

  // Optional highlight helper (safe if missing)
  if (typeof enableActiveStageHighlight === "function") {
    enableActiveStageHighlight(nav, navSections);
  }
}

function enableActiveStageHighlight(navEl, stageSections) {
  const tabs = Array.from(navEl.querySelectorAll(".stage-tab"));
  const tabById = new Map(tabs.map((t) => [t.dataset.target, t]));

  function setActive(id) {
    tabs.forEach((t) => t.setAttribute("aria-current", "false"));
    const active = tabById.get(id);
    if (!active) return;
    active.setAttribute("aria-current", "true");
    active.scrollIntoView({
      behavior: "smooth",
      inline: "center",
      block: "nearest",
    });
  }

  const io = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (visible?.target?.id) setActive(visible.target.id);
    },
    {
      rootMargin: "-20% 0px -70% 0px",
      threshold: 0.01,
    }
  );

  stageSections.forEach((sec) => io.observe(sec));
  if (stageSections[0]?.id) setActive(stageSections[0].id);
}
