"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const renderIcons = () => {
    if (typeof lucide !== "undefined" && typeof lucide.createIcons === "function") {
      lucide.createIcons();
    }
  };
  renderIcons();

  // Sticky navbar scroll state
  const navbar = document.getElementById("siteNavbar");
  if (navbar) {
    const syncNavbarScroll = () => {
      navbar.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    syncNavbarScroll();
    window.addEventListener("scroll", syncNavbarScroll, { passive: true });
  }

  // Light / deep-plum dark theme toggle
  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle instanceof HTMLButtonElement) {
    const syncThemeIcons = () => {
      const isDark = document.documentElement.getAttribute("data-theme") === "dark";
      const darkIcon = themeToggle.querySelector(".theme-icon-dark");
      const lightIcon = themeToggle.querySelector(".theme-icon-light");
      if (darkIcon && lightIcon) {
        darkIcon.classList.toggle("d-none", isDark);
        lightIcon.classList.toggle("d-none", !isDark);
      }
      themeToggle.setAttribute("aria-pressed", String(isDark));
    };

    syncThemeIcons();
    themeToggle.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try {
        localStorage.setItem("cifake-theme", next);
      } catch (e) {}
      syncThemeIcons();
    });
  }

  // Scroll reveal (triggers once per element)
  const revealTargets = document.querySelectorAll("[data-reveal]");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (revealTargets.length > 0) {
    if (reducedMotion || typeof IntersectionObserver === "undefined") {
      revealTargets.forEach((el) => el.classList.add("is-visible"));
    } else {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -24px 0px" },
      );
      revealTargets.forEach((el) => observer.observe(el));
    }
  }

  // Results dashboard interactions
  const resultsDashboard = document.getElementById("resultsDashboard");
  if (resultsDashboard) {
    const inspectToggle = document.getElementById("imageInspectToggle");
    const dimensionsOutput = document.getElementById("inputDimensions");
    const originalImage = document.getElementById("originalImage");

    if (inspectToggle instanceof HTMLButtonElement) {
      inspectToggle.addEventListener("click", () => {
        const inspecting = resultsDashboard.classList.toggle("is-inspecting");
        inspectToggle.setAttribute("aria-pressed", String(inspecting));
        inspectToggle.innerHTML = inspecting
          ? '<i data-lucide="minimize-2" width="15" height="15" stroke-width="1.75" aria-hidden="true"></i>Fit image to frame'
          : '<i data-lucide="zoom-in" width="15" height="15" stroke-width="1.75" aria-hidden="true"></i>Inspect at full resolution';
        renderIcons();
      });
    }

    if (
      dimensionsOutput &&
      originalImage instanceof HTMLImageElement
    ) {
      const updateDimensions = () => {
        if (originalImage.naturalWidth > 0 && originalImage.naturalHeight > 0) {
          dimensionsOutput.textContent =
            `${originalImage.naturalWidth} × ${originalImage.naturalHeight} px`;
        }
      };

      originalImage.addEventListener("load", updateDimensions);
      updateDimensions();
    }
  }

  // Upload form & drop zone interactions
  const uploadForm = document.getElementById("uploadForm");
  if (!uploadForm) {
    return;
  }

  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("imageInput");
  const browseButton = document.getElementById("browseButton");
  const removeFileButton = document.getElementById("removeFileButton");
  const uploadError = document.getElementById("uploadError");
  const previewContainer = document.getElementById("previewContainer");
  const imagePreview = document.getElementById("imagePreview");
  const fileDetails = document.getElementById("fileDetails");
  const submitButton = document.getElementById("submitButton");
  const submitButtonText = document.getElementById("submitButtonText");
  const submitSpinner = document.getElementById("submitSpinner");
  const loadingOverlay = document.getElementById("loadingOverlay");

  if (
    !dropZone ||
    !(fileInput instanceof HTMLInputElement) ||
    !(browseButton instanceof HTMLButtonElement) ||
    !(removeFileButton instanceof HTMLButtonElement) ||
    !uploadError ||
    !previewContainer ||
    !(imagePreview instanceof HTMLImageElement) ||
    !fileDetails ||
    !(submitButton instanceof HTMLButtonElement) ||
    !submitButtonText ||
    !submitSpinner ||
    !loadingOverlay
  ) {
    return;
  }

  const allowedExtensions = new Set(
    (uploadForm.dataset.allowedExtensions || "")
      .split(",")
      .map((extension) => extension.trim().toLowerCase())
      .filter(Boolean),
  );
  const maxFileSize = Number(uploadForm.dataset.maxFileSize);
  const bytesPerKilobyte = 1024;
  const kilobytesPerMegabyte = 1024;
  let dragDepth = 0;

  function showError(message) {
    uploadError.textContent = message;
    uploadError.classList.remove("d-none");
    fileInput.setAttribute("aria-invalid", "true");
  }

  function clearError() {
    uploadError.textContent = "";
    uploadError.classList.add("d-none");
    fileInput.removeAttribute("aria-invalid");
  }

  function formatFileSize(bytes) {
    if (bytes < bytesPerKilobyte) {
      return `${bytes} B`;
    }
    if (bytes < bytesPerKilobyte * kilobytesPerMegabyte) {
      return `${(bytes / bytesPerKilobyte).toFixed(1)} KB`;
    }
    return `${(bytes / (bytesPerKilobyte * kilobytesPerMegabyte)).toFixed(1)} MB`;
  }

  function clearPreview() {
    imagePreview.removeAttribute("src");
    previewContainer.classList.add("d-none");
    fileDetails.textContent = "";
  }

  function previewFile(file) {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      if (fileInput.files?.[0] !== file || typeof reader.result !== "string") {
        return;
      }
      imagePreview.src = reader.result;
      previewContainer.classList.remove("d-none");
    });
    reader.addEventListener("error", () => {
      if (fileInput.files?.[0] === file) {
        clearPreview();
        showError("We couldn't read that image file. Please try another JPEG or PNG.");
      }
    });
    reader.readAsDataURL(file);
  }

  function validateFile(file) {
    const extension = file.name.split(".").pop()?.toLowerCase() || "";
    if (!allowedExtensions.has(extension)) {
      const extensions = [...allowedExtensions].map((item) => `.${item}`).join(", ");
      clearPreview();
      showError(`That file type isn't supported. Please choose a ${extensions} image.`);
      return false;
    }

    fileDetails.textContent = `${file.name} · ${formatFileSize(file.size)}`;
    previewFile(file);

    if (file.size > maxFileSize) {
      showError(`That image is a bit too large. Please keep uploads under ${formatFileSize(maxFileSize)}.`);
      return false;
    }

    clearError();
    return true;
  }

  function selectFile(file) {
    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
    validateFile(file);
  }

  browseButton.addEventListener("click", (event) => {
    event.stopPropagation();
    fileInput.click();
  });

  dropZone.addEventListener("click", (event) => {
    if (event.target instanceof Element && event.target.closest("button")) {
      return;
    }
    fileInput.click();
  });

  dropZone.addEventListener("keydown", (event) => {
    if (event.target === dropZone && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (file) {
      validateFile(file);
    } else {
      clearPreview();
      clearError();
    }
  });

  removeFileButton.addEventListener("click", () => {
    fileInput.value = "";
    clearPreview();
    clearError();
    fileInput.click();
  });

  dropZone.addEventListener("dragenter", (event) => {
    event.preventDefault();
    dragDepth += 1;
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = "copy";
    }
  });

  dropZone.addEventListener("dragleave", (event) => {
    event.preventDefault();
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) {
      dropZone.classList.remove("drag-over");
    }
  });

  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dragDepth = 0;
    dropZone.classList.remove("drag-over");
    const file = event.dataTransfer?.files[0];
    if (file) {
      selectFile(file);
    }
  });

  uploadForm.addEventListener("submit", (event) => {
    const file = fileInput.files?.[0];
    if (!file) {
      event.preventDefault();
      showError("Please choose a JPEG or PNG image before classifying.");
      return;
    }
    if (!validateFile(file)) {
      event.preventDefault();
      return;
    }

    clearError();
    submitButton.disabled = true;
    submitButtonText.textContent = "Classifying...";
    submitSpinner.classList.remove("d-none");
    loadingOverlay.classList.remove("d-none");
    loadingOverlay.setAttribute("aria-hidden", "false");
  });
});
