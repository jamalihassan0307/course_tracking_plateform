document.addEventListener("DOMContentLoaded", function () {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Add animation to cards
  const animateCards = () => {
    const cards = document.querySelectorAll(".card");
    cards.forEach((card, index) => {
      card.style.opacity = "0";
      card.style.transform = "translateY(20px)";
      card.style.transition = "opacity 0.5s ease, transform 0.5s ease";

      setTimeout(() => {
        card.style.opacity = "1";
        card.style.transform = "translateY(0)";
      }, 100 * index);
    });
  };

  // Run animation on page load
  animateCards();

  // Progress bar animation
  const animateProgressBars = () => {
    const progressBars = document.querySelectorAll(".progress-bar");
    progressBars.forEach((progressBar) => {
      const value = progressBar.getAttribute("aria-valuenow");
      progressBar.style.width = "0%";

      setTimeout(() => {
        progressBar.style.width = value + "%";
        progressBar.style.transition = "width 1s ease-in-out";
      }, 300);
    });
  };

  // Run progress bar animation
  animateProgressBars();

  // Rating script
  const ratingInputs = document.querySelectorAll('input[name="rating"]');
  const ratingLabels = document.querySelectorAll(".rating-label");

  if (ratingInputs.length > 0) {
    ratingInputs.forEach((input, index) => {
      input.addEventListener("change", function () {
        // Reset all stars
        ratingLabels.forEach((label) => {
          label.classList.remove("text-warning");
        });

        // Light up stars up to the selected one
        const rating = parseInt(this.value);
        for (let i = 0; i < rating; i++) {
          ratingLabels[i].classList.add("text-warning");
        }
      });
    });
  }

  // Enrollment request confirmation
  const enrollmentForms = document.querySelectorAll(".enrollment-form");
  if (enrollmentForms.length > 0) {
    enrollmentForms.forEach((form) => {
      form.addEventListener("submit", function (e) {
        if (
          !confirm(
            "Are you sure you want to request enrollment for this course?"
          )
        ) {
          e.preventDefault();
        }
      });
    });
  }

  // Module completion confirmation
  const moduleCompletionForms = document.querySelectorAll(
    ".module-completion-form"
  );
  if (moduleCompletionForms.length > 0) {
    moduleCompletionForms.forEach((form) => {
      form.addEventListener("submit", function (e) {
        if (!confirm("Mark this module as completed?")) {
          e.preventDefault();
        }
      });
    });
  }

  // Auto-hide alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  if (alerts.length > 0) {
    alerts.forEach((alert) => {
      setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }, 5000);
    });
  }
});
