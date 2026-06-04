var DOMHelpers = require('./helpers/dom.helpers.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

function fillSection(name, callback){
  let path = location.pathname
  path += path.endsWith("/") ? "" : "/"
  $.getJSON(path + name).then(function (data) {
    if (name == 'celery' && (!data.queues || !Boolean(data.queues.length))){
      // If no data was returned, don't redraw the section.
      return
    }
    DOMHelpers.changeHTML('#' + name, HandlebarsHelpers.renderTemplate('#' + name + '-template', data));

    if (callback){
      callback();
    }
  });
}

// Start an auto-refresh timer that only fetches while the data is actually
// being looked at: skip when the browser tab is hidden, or when the section's
// sub-tab is not the visible one. The interval keeps running so the refresh
// resumes automatically when the section becomes visible again.
function autoRefresh(fn, ms, sectionId){
  return setInterval(function(){
    if (document.hidden) return;
    if (!sectionVisible(sectionId)) return;
    fn();
  }, ms);
}

function sectionVisible(sectionId){
  let pane = document.getElementById(sectionId).closest('.tab-pane');
  return Boolean(pane && pane.classList.contains('active'));
}

// Each tab's sections are loaded lazily, the first time the tab is opened
// (see the bottom of this file), rather than all at once on page load.
const tabSections = {
  '#celery_data': ['celery_queues', 'celery'],
  '#rate-limits-pane': ['rate_limits'],
  '#capture-job-pane': ['job_queue'],
  '#capture-error-pane': ['capture_errors'],
  '#days-pane': ['days'],
  '#random-pane': ['random'],
  '#emails-pane': ['emails'],
};
const loadedTabs = new Set();
function loadTab(hash){
  if (loadedTabs.has(hash) || !tabSections[hash]) return;
  loadedTabs.add(hash);
  tabSections[hash].forEach(name => fillSection(name));
}

// Refresh the celery queue job counts on button press.
// Loaded once on page load above; auto-refresh is opt-in to avoid constant polling.
function refresh_celery_queues(){
  return autoRefresh(function(){ fillSection("celery_queues")}, 2000, "celery_queues");
}
let celery_queues_refresh = null;
document.getElementById('toggle-queues-auto-refresh').addEventListener('click', (e) => {
  if (celery_queues_refresh){
    clearInterval(celery_queues_refresh);
    celery_queues_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 2s)';
  } else {
    celery_queues_refresh = refresh_celery_queues();
    e.target.innerText = 'Stop Auto-Refresh';
  }
})

// Start refreshing the list of celery workers and the jobs they are processing on button press
function refresh_celery_jobs(){
  return autoRefresh(function(){ fillSection("celery")}, 2000, "celery");
}
let celery_tasks_refresh = null;
document.getElementById('toggle-tasks-auto-refresh').addEventListener('click', (e) => {
  if (celery_tasks_refresh){
    clearInterval(celery_tasks_refresh);
    celery_tasks_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 2s)';
  } else {
    celery_tasks_refresh = refresh_celery_jobs();
    e.target.innerText = 'Stop Auto-Refresh';
  }
})

// Refresh the rate limits once, on button press
// or, start auto-refreshing every 20s, when the other button is pressed
function refresh_rate_limits(){
  let status = document.getElementById('rate-limits-status')
  status.innerText = 'Refreshing...';
  fillSection("rate_limits", () => {
    status.innerText = 'Refreshed!';
    setTimeout(()=> status.innerText = '', 2000);
  });
}
function auto_refresh_rate_limits(){
  return autoRefresh(function(){ refresh_rate_limits()}, 15000, "rate_limits");
}
document.getElementById('refresh-rate-limits').addEventListener('click', (e) => {
  refresh_rate_limits()
})
let rate_limits_refresh = null;
document.getElementById('auto-refresh-rate-limits').addEventListener('click', (e) => {
  if (rate_limits_refresh){
    clearInterval(rate_limits_refresh);
    rate_limits_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 15s)';
  } else {
    e.target.innerText = 'Stop Auto-Refresh';
    refresh_rate_limits()
    rate_limits_refresh = auto_refresh_rate_limits();
  }
})


// Start refreshing the list of capture jobs on button press
function refresh_capture_jobs(){
  return autoRefresh(function(){ fillSection("job_queue")}, 2000, "job_queue");
}
let capture_jobs_refresh = null;
document.getElementById('toggle-capture-jobs-auto-refresh').addEventListener('click', (e) => {
  if (capture_jobs_refresh){
    clearInterval(capture_jobs_refresh);
    capture_jobs_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 2s)';
  } else {
    capture_jobs_refresh = refresh_capture_jobs();
    e.target.innerText = 'Stop Auto-Refresh';
  }
})


// Refresh the capture errors once, on button press
// or, start auto-refreshing every 15s, when the other button is pressed
function refresh_capture_errors(){
  let status = document.getElementById('capture-errors-status')
  status.innerText = 'Refreshing...';
  fillSection("capture_errors", () => {
    status.innerText = 'Refreshed!';
    setTimeout(()=> status.innerText = '', 2000);
  });
}
function auto_refresh_capture_errors(){
  return autoRefresh(function(){ refresh_capture_errors()}, 15000, "capture_errors");
}
document.getElementById('refresh-capture-errors').addEventListener('click', (e) => {
  refresh_capture_errors()
})
let capture_errors_refresh = null;
document.getElementById('auto-refresh-capture-errors').addEventListener('click', (e) => {
  if (capture_errors_refresh){
    clearInterval(capture_errors_refresh);
    capture_errors_refresh = null;
    e.target.innerText = 'Start Auto-Refresh (every 15s)';
  } else {
    e.target.innerText = 'Stop Auto-Refresh';
    refresh_capture_errors()
    capture_errors_refresh = auto_refresh_capture_errors();
  }
})



// Load a tab's sections when it is opened.
document.querySelector('.nav-tabs').addEventListener('click', (e) => {
  window.location.hash = e.target.hash;
  loadTab(e.target.hash);
})

// Select the tab specified in the hash, if present on page load
if (window.location.hash) {
    let tabNav = document.querySelector(`a[href="${window.location.hash}"]`);
    if (tabNav) {
      tabNav.click();
    }
}

// Load the initially-visible tab's sections (the hash tab if valid, else the default).
loadTab(tabSections[window.location.hash] ? window.location.hash : '#celery_data');
