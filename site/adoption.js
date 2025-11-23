document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("assets/adoption.json", { cache: "no-store" });
    if (!res.ok) {
      console.error("Failed to load adoption.json", res.status, res.statusText);
      return;
    }
    const adopt = await res.json();
    renderAdoptionDetails(adopt);
  } catch (err) {
    console.error("Error loading adoption.json", err);
  }
});

function renderAdoptionDetails(adopt) {
  if (!adopt) return;

  const { litter = {}, status = {}, policies = {}, contact = {} } = adopt;
  const homePrefs = policies.home_preferences || {};

  // --- Elements ---
  const bannerEl = document.getElementById("adopt-banner-details");
  const litterSummaryEl = document.getElementById("litter-summary");
  const statusSummaryEl = document.getElementById("status-summary");
  const homeIdealFamilyEl = document.getElementById("home-ideal-family");
  const homeIdealEnvEl = document.getElementById("home-ideal-environment");
  const homeOutdoorListEl = document.getElementById("home-outdoor-options");
  const homeSafetyEl = document.getElementById("home-safety-notes");
  const rehomingCopyEl = document.getElementById("rehoming-copy");
  const rehomingFeesEl = document.getElementById("rehoming-fees");
  const contactPrefaceEl = document.getElementById("contact-preface");
  const emailEl = document.getElementById("adopt-email");

  // --- Litter summary banner ---
  const bannerText = [
    litter.total && `${litter.total} kittens`,
    litter.boys != null && litter.girls != null
      ? `${litter.boys} boys / ${litter.girls} girls`
      : null,
    litter.born_on && `born ${litter.born_on}`,
    litter.ready_window && `ready ${litter.ready_window}`,
    litter.location && litter.location,
  ]
    .filter(Boolean)
    .join(" • ");

  if (bannerEl && bannerText) {
    bannerEl.textContent = bannerText;
  }

  if (litterSummaryEl && bannerText) {
    litterSummaryEl.textContent = bannerText;
  }

  if (
    statusSummaryEl &&
    (status.available != null || status.reserved != null)
  ) {
    const parts = [];
    if (status.available != null) parts.push(`${status.available} available`);
    if (status.reserved != null) parts.push(`${status.reserved} reserved`);
    statusSummaryEl.textContent = parts.join(" • ");
  }

  // --- Home preferences ---
  if (homeIdealFamilyEl && homePrefs.ideal_family) {
    homeIdealFamilyEl.textContent = homePrefs.ideal_family;
  }

  if (homeIdealEnvEl && homePrefs.ideal_environment) {
    homeIdealEnvEl.textContent = homePrefs.ideal_environment;
  }

  if (homeOutdoorListEl && Array.isArray(homePrefs.outdoor_options)) {
    homeOutdoorListEl.innerHTML = "";
    homePrefs.outdoor_options.forEach((opt) => {
      const li = document.createElement("li");
      li.textContent = opt;
      homeOutdoorListEl.appendChild(li);
    });
  }

  if (homeSafetyEl && Array.isArray(homePrefs.safety_notes)) {
    homeSafetyEl.textContent = homePrefs.safety_notes.join(" ");
  }

  // --- Rehoming ---
  if (rehomingCopyEl) {
    // You previously had this logic inline; keep it consistent:
    const base =
      "We’re not breeders — just rehoming our family cat’s litter into caring homes.";
    const siblingNote = policies.sibling_adopting_together
      ? " We prefer you adopt a pair of siblings but not required."
      : "";
    rehomingCopyEl.textContent = base + siblingNote;
  }

  // Optional fee fields if you decide to add them to adoption.json later
  if (rehomingFeesEl) {
    const feeParts = [];
    if (policies.rehoming_fee_each != null) {
      feeParts.push(
        `Standard rehoming fee: $${policies.rehoming_fee_each} per kitten.`
      );
    }
    if (policies.rehoming_fee_pair != null) {
      feeParts.push(
        `Sibling pair rate: $${policies.rehoming_fee_pair} for two kittens.`
      );
    }
    if (feeParts.length) {
      rehomingFeesEl.textContent = feeParts.join(" ");
    }
  }

  // --- Contact ---
  if (contactPrefaceEl && contact.preface) {
    contactPrefaceEl.textContent = contact.preface;
  }

  if (emailEl && contact.email) {
    emailEl.href = `mailto:${contact.email}?subject=${encodeURIComponent(
      "Sunny Tabbies adoption inquiry"
    )}`;
  }
}
