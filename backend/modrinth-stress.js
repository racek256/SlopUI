// Reproduces the Modrinth search -> download-modal stress test under Lightpanda,
// including the GPP-consent workaround needed to render the discover page.

const page = new Page();

// Homepage loads cleanly; use it to install the Google GPP consent stub and access
// the Nuxt router in the SAME JS context, so the discover page can render.
await page.goto("https://modrinth.com/");
page.evaluate(`(function () {
  if (typeof window.__gpp !== "function") {
    var s = function () {};
    s.command = s;
    s.query = function (cmd, cb) {
      if (cb) cb({ gdprApplies: false, cmpStatus: "error", cmpDisplayStatus: "hidden", applicableSections: [0], signalStatus: "not ready" }, true);
    };
    window.__gpp = s;
  }
})();`);

// Direct goto of /discover crashes with "TypeError: Illegal invocation" because the
// GPP stub isn't installed before app init. Route there with the real Vue Router
// (keeps window.__gpp alive) to search "mod essentials".
const pushed = page.evaluate(`(async function () {
  if (typeof window.useNuxtApp === "function") {
    const nuxt = await window.useNuxtApp();
    if (nuxt && nuxt.$router && typeof nuxt.$router.push === "function") {
      await nuxt.$router.push("/discover/mods?q=mod+essentials");
      return location.href;
    }
  }
  return null;
})()`);

// Open the top result (Fuji Essentials) via the SPA router so the stub persists.
page.evaluate(`(async function () {
  const nuxt = await window.useNuxtApp();
  await nuxt.$router.push("/mod/fuji");
  return location.href;
})()`);

// Confirm the page and the Download button are present.
const downloadBtn = page.findElement({ role: "button", name: "Download" });
const dl = downloadBtn && downloadBtn[0];

// Open the Download dialog and capture whatever platform/version options render.
let modalText = null;
if (dl) {
  page.click(dl.backendNodeId ? { backendNodeId: dl.backendNodeId } : { selector: "button" });
  const dialog = page.extract({ dialog: "[role='dialog']" });
  modalText = dialog.dialog;
}

// Expected result: the dialog shows "Select platform"/"Select game version", but the
// option lists (client/neoforge loaders, 1.21.1 versions) do NOT render because
// Modrinth's dropdowns hit "TypeError: Illegal invocation" in this browser.
return { searchUrl: pushed, downloadModal: modalText };
