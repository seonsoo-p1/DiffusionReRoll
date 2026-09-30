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

document.querySelectorAll("[data-video-comparison]").forEach((comparison) => {
  const videos = Array.from(comparison.querySelectorAll("video"));
  const controls = comparison.querySelector("[data-video-controls]");
  const status = comparison.querySelector("[data-video-status]");

  if (!videos.length || !controls || !status) return;

  let operation = 0;
  let pending = null;
  let playbackError = "";

  const pauseVideos = () => videos.forEach((video) => video.pause());

  const cancelPending = () => {
    operation += 1;
    if (pending) pending.abort();
    pending = null;
  };

  const describePlayback = () => {
    if (pending) return;
    if (playbackError) {
      status.textContent = playbackError;
      return;
    }
    const finished = videos.filter((video) => video.ended).length;
    const playing = videos.filter((video) => !video.paused && !video.ended).length;

    if (finished === videos.length) {
      status.textContent = "All clips finished. Select Play together to watch again.";
    } else if (playing === videos.length - finished && playing > 0) {
      status.textContent = finished
        ? "Clips playing. Finished clips hold their final frame."
        : "All clips playing.";
    } else if (playing > 0) {
      status.textContent = "Some clips are paused. Select Restart to compare from the beginning.";
    } else {
      status.textContent = "All clips paused.";
    }
  };

  // Wait for every clip before starting a comparison, including on slow connections.
  const waitUntilReady = (video, signal) => new Promise((resolve, reject) => {
    const cleanup = () => {
      video.removeEventListener("canplay", ready);
      video.removeEventListener("seeked", ready);
      video.removeEventListener("error", failed);
      signal.removeEventListener("abort", aborted);
    };
    const ready = () => {
      if (video.readyState < 3 || video.seeking) return;
      cleanup();
      resolve();
    };
    const failed = () => {
      cleanup();
      reject(new Error("Video could not load."));
    };
    const aborted = () => {
      cleanup();
      reject(new DOMException("Playback cancelled.", "AbortError"));
    };

    if (signal.aborted) return aborted();
    if (video.error) return failed();
    if (video.readyState >= 3 && !video.seeking) return ready();

    video.addEventListener("canplay", ready);
    video.addEventListener("seeked", ready);
    video.addEventListener("error", failed);
    signal.addEventListener("abort", aborted, { once: true });
    video.preload = "auto";
    if (video.readyState === 0) video.load();
  });

  const playVideos = async (restart = false) => {
    cancelPending();
    playbackError = "";
    const currentOperation = operation;
    const controller = new AbortController();
    pending = controller;
    pauseVideos();

    const reset = restart || videos.every((video) => video.ended);
    if (reset) videos.forEach((video) => { video.currentTime = 0; });
    const active = reset ? videos : videos.filter((video) => !video.ended);
    status.textContent = "Loading clips for comparison…";

    const loaded = await Promise.allSettled(active.map((video) =>
      waitUntilReady(video, controller.signal).catch((error) => {
        controller.abort();
        throw error;
      })
    ));
    if (currentOperation !== operation) return;

    if (loaded.some((result) => result.status === "rejected")) {
      pending = null;
      playbackError = "Could not load all clips. Use the individual video controls to view available clips.";
      describePlayback();
      return;
    }

    const started = await Promise.allSettled(
      active.map((video) => Promise.resolve().then(() => video.play()))
    );
    if (currentOperation !== operation) return;
    pending = null;

    if (started.some((result) => result.status === "rejected")) {
      playbackError = "Playback could not start for every clip. Try Play together again or use the individual video controls.";
      pauseVideos();
    }
    describePlayback();
  };

  const startComparison = (restart) => {
    void playVideos(restart).catch(() => {
      cancelPending();
      playbackError = "Comparison playback is unavailable. Use the individual video controls.";
      pauseVideos();
      describePlayback();
    });
  };

  controls.addEventListener("click", (event) => {
    const button = event.target.closest("[data-video-action]");
    if (!button || !controls.contains(button)) return;

    switch (button.dataset.videoAction) {
      case "play":
        startComparison(false);
        break;
      case "restart":
        startComparison(true);
        break;
      case "pause":
        cancelPending();
        playbackError = "";
        pauseVideos();
        status.textContent = "All clips paused.";
        break;
    }
  });

  videos.forEach((video) => {
    video.addEventListener("play", () => {
      if (!pending) playbackError = "";
      describePlayback();
    });
    ["pause", "ended"].forEach((event) => {
      video.addEventListener(event, describePlayback);
    });
  });
  controls.hidden = false;
});
