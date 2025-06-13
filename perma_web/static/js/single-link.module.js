var resizeTimeout, wrapper;

export var detailsButton = document.getElementById("details-button");
var detailsTray = document.getElementById("collapse-details");
var viewMode = document.getElementsByClassName("view-mode")[0];

var copyBtn = document.getElementById('copy-link-btn');
var copyText = copyBtn?.querySelector('.copy-text');
var copiedText = copyBtn?.querySelector('.copied-text');

function init () {
  adjustTopMargin();
  var clicked = false;
  if (detailsButton) {
    detailsButton.onclick = function () {
      clicked = !clicked;
      handleShowDetails(clicked);
    };
  }

  initCopyLink();

  window.onresize = function(){
    if (resizeTimeout != null)
      clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(adjustTopMargin, 200);
  };
}

export function handleShowDetails (open) {
  detailsButton.textContent = open ? "Hide record details":"Show record details";
  detailsTray.style.display = open ? "block" : "none";
  viewMode.style.display = open ? "none" : "block" ;
}

function adjustTopMargin () {
  let wrapper = document.getElementsByClassName("capture-wrapper")[0];
  let header = document.getElementsByTagName('header')[0];
  if (!wrapper) return;
  wrapper.style.marginTop = `${header.offsetHeight}px`;
  wrapper.style.height = `calc(100% - ${header.offsetHeight}px)`;
}

function initCopyLink() {
  if (copyBtn) {
    copyBtn.addEventListener('click', function() {
      const permalinkUrl = document.getElementById('permalink-url').textContent;
      
      // Modern clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(permalinkUrl).then(function() {
          showCopiedFeedback();
        }).catch(function(err) {
          console.error('Failed to copy: ', err);
          fallbackCopyTextToClipboard(permalinkUrl);
        });
      } else {
        // Fallback for older browsers
        fallbackCopyTextToClipboard(permalinkUrl);
      }
    });
  }
}

function showCopiedFeedback() {
  if (copyText && copiedText) {
    copyText.style.display = 'none';
    copiedText.style.display = 'inline';
    
    // Reset after 2 seconds
    setTimeout(function() {
      copyText.style.display = 'inline';
      copiedText.style.display = 'none';
    }, 2000);
  }
}

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    // This is deprecated, but it's a fallback for older browsers 
    // that don't support the clipboard API. It creates a temporary 
    // textarea element, copies the text to it, and then removes it.
    const successful = document.execCommand('copy');
    if (successful) {
      showCopiedFeedback();
    }
  } catch (err) {
    console.error('Fallback copy failed: ', err);
  }
  
  document.body.removeChild(textArea);
}

init();
