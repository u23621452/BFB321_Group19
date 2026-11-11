/* Job files page: create a job (flow 1) and browse all job files. */
(function () {
  'use strict';
  var el = SF.el;
  function byId(id) { return document.getElementById(id); }

  var form = byId('jobForm');
  var linesBox = byId('bomLines');
  var linesError = byId('error-lines');
  var resultBox = byId('resultBox');
  var saveBtn = byId('saveBtn');
  var jobBody = byId('jobBody');
  var pager = byId('jobPager');

  var products = [];          // every product, for the BOM drop-downs
  var lineCounter = 0;
  var state = { page: 1, search: '', status: '' };

  /* ---------- the BOM lines in the form ---------- */

  function addLine() {
    var n = ++lineCounter;

    var select = el('select', { class: 'form-select', id: 'sku' + n, required: '' });
    select.append(el('option', { value: '', text: 'Choose SKU…' }));
    products.forEach(function (p) {
      select.append(el('option', { value: p.sku, text: p.sku + ' – ' + p.description }));
    });

    var qty = el('input', { type: 'number', class: 'form-control', id: 'qty' + n,
      min: '1', step: '1', required: '', inputmode: 'numeric', placeholder: 'Qty' });

    var remove = el('button', { type: 'button', class: 'btn btn-outline-danger', 'aria-label': 'Remove BOM line ' + n });
    remove.append(el('i', { class: 'bi bi-trash', 'aria-hidden': 'true' }));
    remove.addEventListener('click', function () { row.remove(); });

    var row = el('div', { class: 'sf-bom-row' }, [
      el('div', {}, [
        el('label', { for: 'sku' + n, class: 'visually-hidden', text: 'SKU for line ' + n }), select,
        el('div', { class: 'invalid-feedback', text: 'Choose a SKU (each SKU once).' })]),
      el('div', {}, [
        el('label', { for: 'qty' + n, class: 'visually-hidden', text: 'Quantity for line ' + n }), qty,
        el('div', { class: 'invalid-feedback', text: 'Whole number, 1 or more.' })]),
      remove
    ]);
    linesBox.append(row);
  }

  function readLines() {
    return Array.from(linesBox.querySelectorAll('.sf-bom-row')).map(function (row) {
      return {
        sku: row.querySelector('select').value,
        qty: parseInt(row.querySelector('input').value, 10),
        select: row.querySelector('select')
      };
    });
  }

  /* ---------- checking the form before it is sent ---------- */

  function showLinesError(message) {
    linesError.textContent = message;
    linesError.classList.toggle('d-none', !message);
    linesError.classList.toggle('d-block', !!message);
  }

  function formIsValid() {
    var lines = readLines();
    var seen = new Set();
    lines.forEach(function (line) {
      line.select.setCustomValidity(line.sku && seen.has(line.sku) ? 'duplicate' : '');
      seen.add(line.sku);
    });

    var start = byId('startDate');
    start.setCustomValidity(start.value && start.value < start.min ? 'past' : '');

    showLinesError(lines.length === 0 ? 'Add at least one BOM line.' : '');
    return form.checkValidity() && lines.length > 0;
  }

  /* ---------- sending the job to the API ---------- */

  function clearForm() {
    form.reset();
    form.classList.remove('was-validated');
    form.querySelectorAll('.is-invalid').forEach(function (box) { box.classList.remove('is-invalid'); });
    showLinesError('');
    linesBox.replaceChildren();
    addLine();
  }

  // Problems found by the server (422) are shown next to the right field.
  function showServerErrors(details) {
    Object.keys(details).forEach(function (field) {
      if (field === 'lines') { showLinesError(details[field]); return; }
      var message = byId('error-' + field);
      var input = field === 'start_date' ? byId('startDate') : byId(field);
      if (message && input) {
        message.textContent = details[field];
        input.classList.add('is-invalid');
      }
    });
  }

  function showResult(job) {
    var short = job.shortages;
    var box = el('div', { class: 'alert alert-' + (short.length ? 'warning' : 'success') + ' mb-0', role: 'status' });
    box.append(el('strong', { text: job.job_number + ' created. ' }));
    if (short.length) {
      box.append('Stock is reserved, but ' + short.length + ' line(s) are short: ' +
        short.map(function (s) { return s.sku + ' (short by ' + s.short_by + ')'; }).join(', ') +
        '. The storeroom queue now shows this shortage.');
    } else {
      box.append('Every BOM line is covered by free stock and is now reserved.');
    }
    resultBox.replaceChildren(box);
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    resultBox.replaceChildren();
    form.classList.add('was-validated');
    form.querySelectorAll('.is-invalid').forEach(function (box) { box.classList.remove('is-invalid'); });

    if (!formIsValid()) {
      var firstBad = form.querySelector(':invalid');
      if (firstBad) { firstBad.focus(); }
      return;
    }

    var body = {
      customer: byId('customer').value.trim(),
      description: byId('description').value.trim(),
      start_date: byId('startDate').value,
      priority: byId('priority').value,
      lines: readLines().map(function (line) { return { sku: line.sku, qty: line.qty }; })
    };

    saveBtn.disabled = true;
    try {
      var job = await SF.api('POST', '/api/jobs', body);
      showResult(job);
      SF.toast(job.job_number + ' saved.');
      clearForm();
      state.page = 1;
      loadJobs();
    } catch (problem) {
      if (problem.status === 422) {
        showServerErrors(problem.details);
      } else {
        resultBox.replaceChildren(el('div', { class: 'alert alert-danger mb-0', role: 'alert',
          text: 'Could not save the job: ' + problem.message }));
      }
    } finally {
      saveBtn.disabled = false;
    }
  });

  form.addEventListener('input', function () {
    if (form.classList.contains('was-validated')) { formIsValid(); }
  });
  byId('addLineBtn').addEventListener('click', addLine);
  byId('clearBtn').addEventListener('click', function () { clearForm(); resultBox.replaceChildren(); });

  /* ---------- the list of all jobs ---------- */

  async function loadJobs() {
    SF.showLoading(jobBody, 5);
    var url = '/api/jobs?per_page=8&page=' + state.page;
    if (state.search) { url += '&search=' + encodeURIComponent(state.search); }
    if (state.status) { url += '&status=' + encodeURIComponent(state.status); }

    try {
      var data = await SF.api('GET', url);
      if (data.items.length === 0) {
        SF.showEmpty(jobBody, 5, 'No job files match your filters.');
        SF.renderPager(pager, data, goToPage);
        return;
      }
      jobBody.replaceChildren(...data.items.map(function (job) {
        var viewBtn = el('button', { type: 'button', class: 'btn btn-sm btn-outline-primary',
          'data-job-detail': job.job_number, text: 'View' });
        return el('tr', {}, [
          el('td', { class: 'fw-semibold', text: job.job_number }),
          el('td', {}, [job.customer, el('div', { class: 'small text-body-secondary', text: job.description })]),
          el('td', { text: SF.formatDate(job.start_date) }),
          el('td', {}, [SF.badge(job.status)]),
          el('td', { class: 'text-end' }, [viewBtn])
        ]);
      }));
      SF.renderPager(pager, data, goToPage);
    } catch (problem) {
      SF.showError(jobBody, 5, 'Could not load job files: ' + problem.message, loadJobs);
      pager.replaceChildren();
    }
  }

  function goToPage(page) { state.page = page; loadJobs(); }

  var searchTimer;
  byId('jobSearch').addEventListener('input', function (event) {
    clearTimeout(searchTimer);      // wait until the person stops typing
    searchTimer = setTimeout(function () {
      state.search = event.target.value.trim();
      state.page = 1;
      loadJobs();
    }, 300);
  });
  byId('jobStatus').addEventListener('change', function (event) {
    state.status = event.target.value;
    state.page = 1;
    loadJobs();
  });

  /* ---------- start ---------- */

  async function start() {
    loadJobs();
    try {
      var data = await SF.api('GET', '/api/inventory?per_page=100');
      products = data.items;
      addLine();
    } catch (problem) {
      saveBtn.disabled = true;
      resultBox.replaceChildren(el('div', { class: 'alert alert-danger mb-0', role: 'alert',
        text: 'Could not load the product list, so new jobs cannot be created: ' + problem.message }));
    }
  }
  start();
})();