/* Custom JavaScript for ToolBoxAI Documentation */

// Add version selector functionality
document.addEventListener('DOMContentLoaded', function() {
  // Enhance code copy functionality
  document.querySelectorAll('.md-clipboard').forEach(function(button) {
    button.addEventListener('click', function() {
      // Show success feedback
      const icon = this.querySelector('.md-clipboard__icon');
      if (icon) {
        icon.textContent = 'check';
        setTimeout(function() {
          icon.textContent = 'content_copy';
        }, 2000);
      }
    });
  });

  // Add anchor links to headings
  document.querySelectorAll('.md-content h2, .md-content h3').forEach(function(heading) {
    if (!heading.querySelector('a.headerlink')) {
      const anchor = document.createElement('a');
      anchor.className = 'headerlink';
      anchor.href = '#' + heading.id;
      anchor.title = 'Permanent link';
      anchor.innerHTML = '¶';
      heading.appendChild(anchor);
    }
  });

  // Add "Edit this page" functionality
  const editButton = document.querySelector('a[title="Edit this page"]');
  if (editButton) {
    editButton.addEventListener('click', function(e) {
      // Track edit button clicks
      if (typeof gtag !== 'undefined') {
        gtag('event', 'click', {
          event_category: 'documentation',
          event_label: 'edit_page',
          value: window.location.pathname
        });
      }
    });
  }

  // Add feedback widget
  addFeedbackWidget();

  // Enhance external links
  document.querySelectorAll('a[href^="http"]').forEach(function(link) {
    if (!link.hostname.includes('toolboxai.com') && !link.hostname.includes('localhost')) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
      link.classList.add('external-link');
    }
  });

  // Add copy button to all code blocks
  enhanceCodeBlocks();

  // Initialize search analytics
  initializeSearchAnalytics();
});

// Add feedback widget to page
function addFeedbackWidget() {
  const content = document.querySelector('.md-content');
  if (!content) return;

  const feedbackWidget = document.createElement('div');
  feedbackWidget.className = 'feedback-widget';
  feedbackWidget.innerHTML = `
    <div class="feedback-question">
      <p>Was this page helpful?</p>
      <div class="feedback-buttons">
        <button class="feedback-btn" data-feedback="yes">👍 Yes</button>
        <button class="feedback-btn" data-feedback="no">👎 No</button>
      </div>
    </div>
    <div class="feedback-thanks" style="display: none;">
      <p>Thank you for your feedback!</p>
    </div>
  `;

  content.appendChild(feedbackWidget);

  // Add event listeners to feedback buttons
  feedbackWidget.querySelectorAll('.feedback-btn').forEach(function(button) {
    button.addEventListener('click', function() {
      const feedback = this.getAttribute('data-feedback');

      // Track feedback
      if (typeof gtag !== 'undefined') {
        gtag('event', 'feedback', {
          event_category: 'documentation',
          event_label: window.location.pathname,
          value: feedback === 'yes' ? 1 : 0
        });
      }

      // Show thank you message
      feedbackWidget.querySelector('.feedback-question').style.display = 'none';
      feedbackWidget.querySelector('.feedback-thanks').style.display = 'block';
    });
  });
}

// Enhance code blocks with better copy functionality
function enhanceCodeBlocks() {
  document.querySelectorAll('pre code').forEach(function(codeBlock) {
    // Add line numbers if not already present
    if (!codeBlock.classList.contains('linenums')) {
      const lines = codeBlock.textContent.split('\n');
      if (lines.length > 5) {
        codeBlock.classList.add('linenums');
      }
    }
  });
}

// Initialize search analytics
function initializeSearchAnalytics() {
  const searchInput = document.querySelector('.md-search__input');
  if (!searchInput) return;

  let searchTimeout;
  searchInput.addEventListener('input', function(e) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function() {
      const query = e.target.value;
      if (query.length > 2 && typeof gtag !== 'undefined') {
        gtag('event', 'search', {
          event_category: 'documentation',
          event_label: query
        });
      }
    }, 1000);
  });
}

// Add smooth scroll behavior for anchor links
document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const targetId = this.getAttribute('href');
    const targetElement = document.querySelector(targetId);

    if (targetElement) {
      targetElement.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });

      // Update URL without triggering navigation
      if (history.pushState) {
        history.pushState(null, null, targetId);
      }
    }
  });
});
