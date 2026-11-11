/* Shared helpers for every page: talking to the API, small HTML builders,
   toasts and the loading / empty / error messages. */
window.SF = window.SF || {};

(function () {
  'use strict';

  /* ---------- Talking to the Flask API ---------- */

  // SF.api('GET', '/api/jobs')  or  SF.api('POST', '/api/jobs', { ... })
  // Gives back the JSON on success. On failure it throws an Error that has
  // .status (HTTP code), .message (text for the user) and .details.
  SF.api = async function (method, url, body) {
    var options = { method: method, headers: {}, credentials: 'same-origin' };
    if (body !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }

    var response;
    try {
      response = await fetch(url, options);
    } catch (networkProblem) {
      var offline = new Error('Cannot reach the server. Check your connection and try again.');
      offline.status = 0;
      offline.details = {};
      throw offline;
    }

    var data = {};
    try { data = await response.json(); } catch (notJson) { /* empty body */ }

    if (response.ok) { return data; }

    var info = data.error || {};
    var error = new Error(info.message || 'Something went wrong.');
    error.status = response.status;
    error.details = info.details || {};

    // logged out (or session expired): go back to the login page
    if (response.status === 401 && location.pathname !== '/login') {
      location.href = '/login';
    }
    throw error;
  };

  /* ---------- Small HTML builders ---------- */

  // SF.el('div', { class: 'card', text: 'Hi' }, [child, child])
  SF.el = function (tag, props, children) {
    var node = document.createElement(tag);
    Object.entries(props || {}).forEach(function (pair) {
      if (pair[0] === 'class') { node.className = pair[1]; }
      else if (pair[0] === 'text') { node.textContent = pair[1]; }
      else { node.setAttribute(pair[0], pair[1]); }
    });
    (children || []).forEach(function (child) { node.append(child); });
    return node;
  };

  var STATUS = {
    reserved: ['primary', 'bookmark-check-fill', 'Reserved'],
    shortage: ['danger', 'exclamation-triangle-fill', 'Shortage'],
    kitting:  ['warning', 'basket-fill', 'Kitting'],
    issued:   ['success', 'check-circle-fill', 'Issued'],
    ok:       ['success', 'check-circle-fill', 'In stock'],
    low:      ['warning', 'exclamation-circle-fill', 'Low'],
    critical: ['danger', 'exclamation-triangle-fill', 'Critical'],
    open:     ['secondary', 'circle', 'Open'],
    done:     ['success', 'check-circle-fill', 'Done']
  };

  SF.badge = function (status) {
    var look = STATUS[status] || ['secondary', 'circle', status];
    var badge = SF.el('span', { class: 'badge sf-badge text-bg-' + look[0] });
    badge.append(SF.el('i', { class: 'bi bi-' + look[1] + ' me-1', 'aria-hidden': 'true' }), look[2]);
    return badge;
  };

  // "2026-11-13" -> "Fri 13 Nov"
  SF.formatDate = function (isoDate) {
    return new Date(isoDate + 'T00:00').toLocaleDateString('en-ZA',
      { weekday: 'short', day: 'numeric', month: 'short' });
  };

  /* ---------- Toast (small pop-up message) ---------- */

  SF.toast = function (message) {
    document.getElementById('sfToastBody').textContent = message;
    bootstrap.Toast.getOrCreateInstance(document.getElementById('sfToast'), { delay: 4000 }).show();
  };

  /* ---------- Loading / empty / error messages ---------- */

  // Fill a table body with ONE message row.
  function messageRow(tbody, columns, content) {
    var cell = SF.el('td', { colspan: columns, class: 'text-center text-body-secondary py-4' });
    cell.append(content);
    tbody.replaceChildren(SF.el('tr', {}, [cell]));
  }

  SF.showLoading = function (tbody, columns) {
    var spinner = SF.el('div', { class: 'spinner-border spinner-border-sm me-2', role: 'status', 'aria-hidden': 'true' });
    var text = SF.el('span', { text: 'Loading…' });
    var wrap = SF.el('span', {}, [spinner, text]);
    messageRow(tbody, columns, wrap);
  };

  SF.showEmpty = function (tbody, columns, message) {
    var wrap = SF.el('span', {}, [
      SF.el('i', { class: 'bi bi-inbox fs-3 d-block mb-1', 'aria-hidden': 'true' }), message]);
    messageRow(tbody, columns, wrap);
  };

  // retry is a function that loads the data again
  SF.showError = function (tbody, columns, message, retry) {
    var button = SF.el('button', { type: 'button', class: 'btn btn-sm btn-outline-danger ms-2', text: 'Try again' });
    button.addEventListener('click', retry);
    var wrap = SF.el('span', { class: 'text-danger' }, [
      SF.el('i', { class: 'bi bi-exclamation-octagon me-1', 'aria-hidden': 'true' }), message, button]);
    messageRow(tbody, columns, wrap);
  };

  // The same three messages for a <ul> or <div> instead of a table.
  SF.showListMessage = function (container, kind, message, retry) {
    var item = SF.el('li', { class: 'list-group-item text-body-secondary' });
    if (kind === 'error') {
      item.className = 'list-group-item text-danger';
      item.append(message + ' ');
      var button = SF.el('button', { type: 'button', class: 'btn btn-sm btn-outline-danger', text: 'Try again' });
      button.addEventListener('click', retry);
      item.append(button);
    } else {
      item.textContent = message;
    }
    container.replaceChildren(item);
  };

  /* ---------- Previous / Next buttons for paged lists ---------- */

  // data is the API answer ({ page, pages, total, ... });
  // goToPage(n) is called when a button is pressed.
  SF.renderPager = function (container, data, goToPage) {
    container.replaceChildren();
    if (data.total === 0) { return; }

    var previous = SF.el('button', { type: 'button', class: 'btn btn-sm btn-outline-secondary', text: '‹ Previous' });
    var next = SF.el('button', { type: 'button', class: 'btn btn-sm btn-outline-secondary', text: 'Next ›' });
    previous.disabled = data.page <= 1;
    next.disabled = data.page >= data.pages;
    previous.addEventListener('click', function () { goToPage(data.page - 1); });
    next.addEventListener('click', function () { goToPage(data.page + 1); });

    container.append(
      SF.el('span', { class: 'small text-body-secondary',
        text: 'Page ' + data.page + ' of ' + data.pages + ' · ' + data.total + ' total' }),
      SF.el('div', { class: 'd-flex gap-2' }, [previous, next]));
  };

  /* ---------- Log out button (in the navbar on every page) ---------- */

  document.addEventListener('DOMContentLoaded', function () {
    var button = document.getElementById('logoutBtn');
    if (!button) { return; }
    button.addEventListener('click', async function () {
      try { await SF.api('POST', '/api/auth/logout'); } catch (problem) { /* leave anyway */ }
      location.href = '/login';
    });
  });
})();