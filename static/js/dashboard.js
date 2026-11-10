/* Dashboard: KPI tiles, next open jobs and critical stock - all from the API. */
(function () {
  'use strict';
  var el = SF.el;

  // [key in the API answer, label, icon, colour, small hint]
  var TILES = [
    ['open_jobs', 'Open job files', 'journal-text', 'primary', ''],
    ['shortage_items', 'Items on shortage', 'exclamation-triangle', 'danger', 'across open jobs'],
    ['upcoming_7_days', 'Starting in 7 days', 'calendar-week', 'success', ''],
    ['reserved_lines', 'Reserved BOM lines', 'bookmark-check', 'info', ''],
    ['shortage_jobs', 'Jobs on shortage', 'bag-x', 'danger', ''],
    ['critical_items', 'Critical stock items', 'box-seam', 'warning', ''],
    ['open_requests', 'Open material requests', 'inbox', 'secondary', ''],
    ['picks_today', 'Picks today', 'check2-circle', 'success', '']
  ];

  var kpiRow = document.getElementById('kpiRow');
  var upcomingBody = document.getElementById('upcomingBody');
  var lowList = document.getElementById('lowList');

  function tile(label, value, icon, tone, hint) {
    var text = el('div', {}, [
      el('div', { class: 'sf-kpi-value', text: value }),
      el('div', { class: 'sf-kpi-label', text: label })
    ]);
    if (hint) { text.append(el('div', { class: 'small text-body-secondary', text: hint })); }
    var body = el('div', { class: 'card-body d-flex align-items-center gap-3' }, [
      el('span', { class: 'sf-kpi-icon text-bg-' + tone }, [el('i', { class: 'bi bi-' + icon, 'aria-hidden': 'true' })]),
      text
    ]);
    return el('div', { class: 'col-6 col-lg-3' }, [el('div', { class: 'card sf-kpi h-100' }, [body])]);
  }

  async function loadKpis() {
    // loading state: the same tiles with "…" as the number
    kpiRow.replaceChildren(...TILES.map(function (t) { return tile(t[1], '…', t[2], t[3], t[4]); }));
    try {
      var data = await SF.api('GET', '/api/kpis');
      kpiRow.replaceChildren(...TILES.map(function (t) { return tile(t[1], data[t[0]], t[2], t[3], t[4]); }));
    } catch (problem) {
      var retry = el('button', { type: 'button', class: 'btn btn-sm btn-outline-danger ms-2', text: 'Try again' });
      retry.addEventListener('click', loadKpis);
      var alertBox = el('div', { class: 'alert alert-danger mb-0', role: 'alert' }, [
        'Could not load the key figures: ' + problem.message, retry]);
      kpiRow.replaceChildren(el('div', { class: 'col-12' }, [alertBox]));
    }
  }

  async function loadUpcoming() {
    SF.showLoading(upcomingBody, 4);
    try {
      var data = await SF.api('GET', '/api/jobs?open=1&per_page=6');
      if (data.items.length === 0) {
        SF.showEmpty(upcomingBody, 4, 'No open job files.');
        return;
      }
      upcomingBody.replaceChildren(...data.items.map(function (job) {
        var jobCell = el('td', { class: 'fw-semibold', text: job.job_number });
        if (job.priority === 'Urgent') {
          jobCell.append(el('span', { class: 'badge text-bg-danger ms-1', text: 'Urgent' }));
        }
        return el('tr', {}, [
          jobCell,
          el('td', {}, [job.customer, el('div', { class: 'small text-body-secondary', text: job.description })]),
          el('td', { text: SF.formatDate(job.start_date) + ' (' + job.days_to_start + ' d)' }),
          el('td', {}, [SF.badge(job.status)])
        ]);
      }));
    } catch (problem) {
      SF.showError(upcomingBody, 4, 'Could not load job files: ' + problem.message, loadUpcoming);
    }
  }

  async function loadCritical() {
    SF.showListMessage(lowList, 'loading', 'Loading…');
    try {
      var data = await SF.api('GET', '/api/inventory?status=critical&per_page=6');
      if (data.items.length === 0) {
        SF.showListMessage(lowList, 'empty', 'No critical items.');
        return;
      }
      lowList.replaceChildren(...data.items.map(function (row) {
        return el('li', { class: 'list-group-item d-flex justify-content-between align-items-center gap-2' }, [
          el('div', {}, [
            el('div', { class: 'fw-semibold', text: row.sku }),
            el('div', { class: 'small text-body-secondary',
              text: row.available + ' free · reorder at ' + Math.round(row.reorder_point) })
          ]),
          SF.badge(row.status)
        ]);
      }));
    } catch (problem) {
      SF.showListMessage(lowList, 'error', 'Could not load stock: ' + problem.message, loadCritical);
    }
  }

  loadKpis();
  loadUpcoming();
  loadCritical();
})();