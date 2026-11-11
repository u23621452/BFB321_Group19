/* Shop-floor scanner page (flow 3): choose a work order, scan or type a
   product code, confirm the pick. The camera scan is simulated: it offers the
   next BOM line that still has to be picked. */
(function () {
  'use strict';
  var el = SF.el;
  function byId(id) { return document.getElementById(id); }

  var jobSelect = byId('scanJob');
  var scanBtn = byId('scanBtn');
  var manualForm = byId('manualForm');
  var manualCode = byId('manualCode');
  var manualBtn = byId('manualBtn');
  var statusBox = byId('scanStatus');
  var panel = byId('pickPanel');
  var qty = byId('pickQty');
  var pickError = byId('pickError');
  var confirmBtn = byId('confirmPick');

  var products = {};     // { sku: product } from the inventory API
  var job = null;        // the selected work order, with its BOM lines
  var current = null;    // the SKU being picked right now
  var cursor = 0;        // which open line the "scan" button offers next

  function lineFor(sku) {
    return job ? job.lines.find(function (line) { return line.sku === sku; }) : null;
  }
  function remaining(line) { return line.qty - line.picked_qty; }

  function showStatus(kind, message, retry) {
    if (!message) { statusBox.replaceChildren(); return; }
    var box = el('div', { class: 'alert alert-' + kind + ' d-flex justify-content-between align-items-center', role: 'alert' },
      [el('span', { text: message })]);
    if (retry) {
      var button = el('button', { type: 'button', class: 'btn btn-sm btn-outline-danger', text: 'Try again' });
      button.addEventListener('click', retry);
      box.append(button);
    }
    statusBox.replaceChildren(box);
  }

  function setControls(enabled) {
    scanBtn.disabled = !enabled;
    manualBtn.disabled = !enabled;
  }

  /* ---------- loading from the API ---------- */

  async function loadProducts() {
    var data = await SF.api('GET', '/api/inventory?per_page=100');
    var requestSelect = byId('reqSku');
    data.items.forEach(function (product) {
      products[product.sku] = product;
      requestSelect.append(el('option', { value: product.sku, text: product.sku + ' – ' + product.description }));
    });
  }

  // Fills the work order list with every job that is not issued yet.
  async function loadJobs() {
    var data = await SF.api('GET', '/api/jobs?open=1&per_page=100');
    jobSelect.replaceChildren(...data.items.map(function (item) {
      var option = el('option', { value: item.job_number, text: item.job_number + ' · ' + item.customer });
      if (item.status === 'kitting') { option.selected = true; }
      return option;
    }));

    if (data.items.length === 0) {
      jobSelect.replaceChildren(el('option', { text: 'No open work orders' }));
      jobSelect.disabled = true;
      setControls(false);
      job = null;
      showStatus('info', 'There are no open work orders to pick for.');
      return;
    }
    jobSelect.disabled = false;
    setControls(true);
    showStatus('', '');
    await loadJob();
  }

  async function loadJob() {
    job = await SF.api('GET', '/api/jobs/' + encodeURIComponent(jobSelect.value));
    cursor = 0;
  }

  async function start() {
    showStatus('secondary', 'Loading work orders…');
    try {
      await loadProducts();
      await loadJobs();
    } catch (problem) {
      jobSelect.replaceChildren(el('option', { text: 'Could not load' }));
      setControls(false);
      showStatus('danger', 'Could not load the work orders: ' + problem.message, start);
    }
  }

  /* ---------- the pick panel ---------- */

  function hidePick() {
    panel.classList.add('d-none');
    pickError.classList.add('d-none');
    current = null;
  }

  function showPick(sku) {
    current = sku;
    var product = products[sku];
    var line = lineFor(sku);
    var need = byId('pickNeed');

    byId('pickTitle').textContent = sku;
    byId('pickDesc').textContent = product.description;
    byId('pickBin').textContent = 'Bin ' + product.bin;
    pickError.classList.add('d-none');
    confirmBtn.disabled = false;

    if (!line) {
      need.className = 'alert alert-warning py-2 mt-3 mb-3';
      need.textContent = 'This item is not on the BOM for ' + job.job_number +
        '. Send a material request to the storeroom instead.';
      confirmBtn.disabled = true;
      qty.value = 1;
    } else if (remaining(line) === 0) {
      need.className = 'alert alert-success py-2 mt-3 mb-3';
      need.textContent = 'Already fully picked for ' + job.job_number + '.';
      confirmBtn.disabled = true;
      qty.value = 1;
    } else {
      need.className = 'alert alert-info py-2 mt-3 mb-3';
      need.textContent = 'Needed for ' + job.job_number + ': ' + line.qty +
        ' · picked ' + line.picked_qty + ' · remaining ' + remaining(line);
      qty.value = Math.max(Math.min(remaining(line), product.on_hand), 1);
    }
    panel.classList.remove('d-none');
    qty.focus();
  }

  /* ---------- scanning and typing a code ---------- */

  scanBtn.addEventListener('click', function () {
    var open = job.lines.filter(function (line) { return remaining(line) > 0; });
    if (open.length === 0) {
      SF.toast('All lines for ' + job.job_number + ' are picked.');
      return;
    }
    showPick(open[cursor++ % open.length].sku);
  });

  manualForm.addEventListener('submit', function (event) {
    event.preventDefault();
    var sku = manualCode.value.trim().toUpperCase();
    manualCode.setCustomValidity(products[sku] ? '' : 'unknown');
    manualForm.classList.add('was-validated');
    if (!manualForm.checkValidity()) { manualCode.focus(); return; }
    manualForm.classList.remove('was-validated');
    manualCode.value = '';
    showPick(sku);
  });
  manualCode.addEventListener('input', function () { manualCode.setCustomValidity(''); });

  byId('qtyMinus').addEventListener('click', function () { qty.value = Math.max((parseInt(qty.value, 10) || 1) - 1, 1); });
  byId('qtyPlus').addEventListener('click', function () { qty.value = (parseInt(qty.value, 10) || 0) + 1; });
  byId('cancelPick').addEventListener('click', hidePick);

  jobSelect.addEventListener('change', async function () {
    hidePick();
    try {
      await loadJob();
    } catch (problem) {
      showStatus('danger', 'Could not load ' + jobSelect.value + ': ' + problem.message);
    }
  });

  /* ---------- confirming a pick ---------- */

  function addToHistory(result, unit) {
    var time = new Date().toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' });
    var item = el('li', { class: 'list-group-item d-flex justify-content-between align-items-center' }, [
      el('div', {}, [el('span', { class: 'fw-semibold', text: result.sku }),
        el('div', { class: 'small text-body-secondary', text: result.job_number + ' · ' + time })]),
      el('span', { class: 'badge text-bg-success', text: '+' + result.picked + ' ' + unit })
    ]);
    var empty = byId('histEmpty');
    if (empty) { empty.remove(); }
    byId('pickHistory').prepend(item);
  }

  confirmBtn.addEventListener('click', async function () {
    var amount = Number(qty.value);
    if (!Number.isInteger(amount) || amount < 1) {
      pickError.textContent = 'Enter a quantity of 1 or more.';
      pickError.classList.remove('d-none');
      qty.focus();
      return;
    }

    confirmBtn.disabled = true;
    pickError.classList.add('d-none');
    try {
      var result = await SF.api('POST', '/api/picks',
        { job_number: jobSelect.value, sku: current, qty: amount });
      products[result.sku].on_hand = result.on_hand_after;
      addToHistory(result, products[result.sku].unit);
      SF.toast('Ledger updated: ' + result.picked + ' × ' + result.sku + ' issued to ' + result.job_number + '.');
      hidePick();

      if (result.job_status === 'issued') {
        SF.toast(result.job_number + ' is fully issued.');
        await loadJobs();            // the finished job leaves the list
      } else {
        await loadJob();             // refresh the picked counts
      }
    } catch (problem) {
      var detail = problem.details && (problem.details.qty || problem.details.sku);
      pickError.textContent = detail || problem.message;
      pickError.classList.remove('d-none');
    } finally {
      confirmBtn.disabled = false;
    }
  });

  /* ---------- request extra material ---------- */

  var requestForm = byId('requestForm');
  var requestModal = bootstrap.Modal.getOrCreateInstance(byId('requestModal'));
  var requestError = byId('reqError');

  requestForm.addEventListener('submit', async function (event) {
    event.preventDefault();
    requestForm.classList.add('was-validated');
    requestError.classList.add('d-none');
    if (!requestForm.checkValidity()) { return; }

    var body = { sku: byId('reqSku').value, qty: Number(byId('reqQty').value), note: byId('reqNote').value.trim() };
    byId('reqSend').disabled = true;
    try {
      await SF.api('POST', '/api/requests', body);
      SF.toast('Request for ' + body.qty + ' × ' + body.sku + ' sent to the storeroom.');
      requestModal.hide();
      requestForm.reset();
      requestForm.classList.remove('was-validated');
    } catch (problem) {
      var messages = Object.values(problem.details || {});
      requestError.textContent = messages.length ? messages.join(' ') : problem.message;
      requestError.classList.remove('d-none');
    } finally {
      byId('reqSend').disabled = false;
    }
  });

  start();
})();