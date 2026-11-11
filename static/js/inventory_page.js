/* Inventory page: stock with reservations, search, filter and paging. */
(function () {
  'use strict';
  var el = SF.el;
  function byId(id) { return document.getElementById(id); }

  var body = byId('invBody');
  var pager = byId('invPager');
  var state = { page: 1, search: '', status: '' };

  async function loadInventory() {
    SF.showLoading(body, 8);
    var url = '/api/inventory?per_page=10&page=' + state.page;
    if (state.search) { url += '&search=' + encodeURIComponent(state.search); }
    if (state.status) { url += '&status=' + encodeURIComponent(state.status); }

    try {
      var data = await SF.api('GET', url);
      if (data.items.length === 0) {
        SF.showEmpty(body, 8, 'No items match your search.');
        pager.replaceChildren();
        return;
      }
      body.replaceChildren(...data.items.map(function (row) {
        return el('tr', {}, [
          el('td', {}, [el('span', { class: 'fw-semibold', text: row.sku }),
            el('div', { class: 'small text-body-secondary', text: row.description })]),
          el('td', { text: row.bin }),
          el('td', { class: 'text-end' }, [row.on_hand + ' ',
            el('span', { class: 'text-body-secondary small', text: row.unit })]),
          el('td', { class: 'text-end', text: row.reserved }),
          el('td', { class: 'text-end fw-semibold', text: row.available }),
          el('td', { class: 'text-end', text: Math.round(row.reorder_point) }),
          el('td', { class: 'text-end' }, [String(row.order_qty),
            el('div', { class: 'small text-body-secondary', text: row.lead_time_days + ' d lead' })]),
          el('td', {}, [SF.badge(row.status)])
        ]);
      }));
      SF.renderPager(pager, data, function (page) { state.page = page; loadInventory(); });
    } catch (problem) {
      SF.showError(body, 8, 'Could not load the inventory: ' + problem.message, loadInventory);
      pager.replaceChildren();
    }
  }

  var searchTimer;
  byId('invSearch').addEventListener('input', function (event) {
    clearTimeout(searchTimer);      // wait until the person stops typing
    searchTimer = setTimeout(function () {
      state.search = event.target.value.trim();
      state.page = 1;
      loadInventory();
    }, 300);
  });
  byId('invStatus').addEventListener('change', function (event) {
    state.status = event.target.value;
    state.page = 1;
    loadInventory();
  });

  loadInventory();
})();