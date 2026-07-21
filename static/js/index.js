const copyButton = document.querySelector("[data-copy-target]");

if (copyButton) {
  copyButton.addEventListener("click", async () => {
    const targetId = copyButton.getAttribute("data-copy-target");
    const target = targetId ? document.getElementById(targetId) : null;
    const status = document.querySelector(".copy-status");

    if (!target) return;

    try {
      await navigator.clipboard.writeText(target.innerText.trim());
      copyButton.textContent = "Copied";
      if (status) status.textContent = "BibTeX copied to clipboard.";
      window.setTimeout(() => {
        copyButton.textContent = "Copy BibTeX";
        if (status) status.textContent = "";
      }, 2200);
    } catch {
      if (status) status.textContent = "Select the BibTeX text and copy it manually.";
    }
  });
}
