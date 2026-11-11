/* Storeroom queue page (flow 2): the jobs starting in the next 7 or 14 days
   and the parts purchasing has to order for them. */
(function () {
  'use strict';
  var el = SF.el;
  function byId(id) { return document.getElementById(id); }

  var queueBody = byId('queueBody');
  var alertBody = byId('alertBody');
  var count = byId('queueCount');
  var onlyShort = byId('onlyShort');

  var days = 7;
  var jobs = [];        // the jobs from the last API answer

  /* ---------- the list of jobs ---------- */

  function showJobs() {
    var shown = onlyShort.checked
      ? jobs.filter(function (job) { return job.shortages.length > 0; })
      : jobs;

    count.textContent = shown.length + (shown.length === 1 ? ' job' : ' jobs') + ' shown';

    if (shown.length === 0) {
      SF.showEmpty(queueBody, 7, onlyShort.checked
        ? 'No jobs with shortages in this window.' : 'No jobs start in this window.');
      return;
    }

    queueBody.replaceChildren(...shown.map(function (job) {
      var jobCell = el('td', { class: 'fw-semibold', text: job.job_number });
      if (job.priority === 'Urgent') {
        jobCell.append(el('span', { class: 'badge text-bg-danger ms-1', text: 'Urgent' }));
      }
      var statusCell = el('td', {}, [SF.badge(job.status)]);
      if (job.shortages.length > 0) {
        statusCell.append(el('div', { class: 'small text-danger mt-1', text: job.shortages.length + ' short' }));
      }
      var openBtn = el('button', { type: 'button', class: 'btn btn-sm btn-outline-primary',
        'data-job-detail': job.job_number, text: 'Open' });

      return el('tr', {}, [
        jobCell,
        el('td', {}, [job.customer, el('div', { class: 'small text-body-secondary', text: job.description })]),
        el('td', { text: SF.formatDate(job.start_date) }),
        el('td', { class: 'text-end', text: job.days_to_start + ' d' }),
        el('td', { class: 'text-end', text: job.line_count }),
        statusCell,
        el('td', { class: 'text-end' }, [openBtn])
      ]);
    }));
  }

  /* ---------- the purchasing alerts ---------- */

  function orderCell(row) {
    if (row.expedite) {
      var badge = el('span', { class: 'badge text-bg-danger' });
      badge.append(el('i', { class: 'bi bi-lightning-charge-fill me-1', 'aria-hidden': 'true' }), 'Expedite now');
      return el('td', {}, [badge,
        el('div', { class: 'small text-body-secondary', text: 'order date was ' + SF.formatDate(row.order_by) })]);
    }
    return el('td', {}, [el('span', { class: 'badge text-bg-warning', text: 'Order by ' + SF.formatDate(row.order_by) })]);
  }

  function showAlerts(summary) {
    if (summary.length === 0) {
      SF.showEmpty(alertBody, 7, 'No shortages in this window. Every job is covered by stock.');
      return;
    }
    alertBody.replaceChildren(...summary.map(function (row) {
      return el('tr', {}, [
        el('td', {}, [el('span', { class: 'fw-semibold', text: row.sku }),
          el('div', { class: 'small text-body-secondary', text: row.description })]),
        el('td', { class: 'text-end fw-semibold text-danger', text: row.short_by }),
        el('td', { text: row.jobs.join(', ') }),
        el('td', { text: SF.formatDate(row.needed_by) }),
        el('td', { class: 'text-end', text: row.lead_time_days + ' d' }),
        el('td', { class: 'text-end', text: row.recommended_order_qty }),
        orderCell(row)
      ]);
    }));
  }

  /* ---------- loading from the API ---------- */

  async function loadQueue() {
    count.textContent = '';
    SF.showLoading(queueBody, 7);
    SF.showLoading(alertBody, 7);
    try {
      var data = await SF.api('GET', '/api/queue?days=' + days);
      jobs = data.jobs;
      showJobs();
      showAlerts(data.shortage_summary);
    } catch (problem) {
      SF.showError(queueBody, 7, 'Could not load the queue: ' + problem.message, loadQueue);
      SF.showError(alertBody, 7, 'Could not load the alerts: ' + problem.message, loadQueue);
    }
  }

  document.querySelectorAll('input[name="window"]').forEach(function (radio) {
    radio.addEventListener('change', function () {
      days = Number(radio.value);
      loadQueue();
    });
  });
  onlyShort.addEventListener('change', showJobs);

  loadQueue();
})();