/* StockFlow - code shared by every page. */

window.SF = JSON.parse(document.body.dataset.sf);

// Make an HTML element:
SF.el = function (tag, attributes, children) {
  var element = document.createElement(tag);
  attributes = attributes || {};
  children = children || [];

  for (var name in attributes) {
    if (name === "class") {
      element.className = attributes[name];
    } else if (name === "text") {
      element.textContent = attributes[name];
    } else {
      element.setAttribute(name, attributes[name]);
    }
  }
  for (var i = 0; i < children.length; i++) {
    element.append(children[i]);
  }
  return element;
};

// status
var STATUS_STYLES = {
  open:     ["secondary", "circle", "Open"],
  reserved: ["primary", "bookmark-check-fill", "Reserved"],
  shortage: ["danger", "exclamation-triangle-fill", "Shortage"],
  kitting:  ["warning", "basket-fill", "Kitting"],
  issued:   ["success", "check-circle-fill", "Issued"]
};

// Make a coloured status label
SF.badge = function (status) {
  var style = STATUS_STYLES[status] || ["secondary", "circle", status];
  var badge = SF.el("span", { class: "badge sf-badge text-bg-" + style[0] });
  var icon = SF.el("i", { class: "bi bi-" + style[1] + " me-1", "aria-hidden": "true" });
  badge.append(icon, style[2]);
  return badge;
};

// Show a small pop-up message at the bottom-right of the screen.
SF.toast = function (message) {
  document.getElementById("sfToastBody").textContent = message;
  var toast = bootstrap.Toast.getOrCreateInstance(document.getElementById("sfToast"), { delay: 4000 });
  toast.show();
};

// Filtering

// Each table remembers its current filters in table.filters
// This function hides every row that does not match all of them.
SF.applyFilters = function (table) {
  var filters = table.filters || {};
  var rows = table.querySelectorAll("tbody tr:not(.sf-empty-row)");
  var visibleCount = 0;

  for (var i = 0; i < rows.length; i++) {
    var row = rows[i];
    var show = true;

    if (filters.search && row.textContent.toLowerCase().indexOf(filters.search) === -1) {
      show = false;
    }
    if (filters.status && row.dataset.status !== filters.status) {
      show = false;
    }
    if (filters.only && row.dataset.status !== filters.only) {
      show = false;
    }
    if (filters.days !== undefined && Number(row.dataset.days) > filters.days) {
      show = false;
    }

    row.classList.toggle("d-none", !show);
    if (show) {
      visibleCount++;
    }
  }

  // Show the "nothing matches" row only when every row is hidden.
  var emptyRow = table.querySelector(".sf-empty-row");
  if (emptyRow) {
    emptyRow.classList.toggle("d-none", visibleCount !== 0);
  }

  table.dispatchEvent(new CustomEvent("sf:filtered", { detail: { visible: visibleCount } }));
};

function setUpFilters() {
  // Search boxes
  var searchBoxes = document.querySelectorAll("[data-filter-table]");
  searchBoxes.forEach(function (box) {
    var table = document.querySelector(box.dataset.filterTable);
    table.filters = table.filters || {};
    box.addEventListener("input", function () {
      table.filters.search = box.value.trim().toLowerCase();
      SF.applyFilters(table);
    });
  });

  // Status drop-downs
  var dropdowns = document.querySelectorAll("[data-status-filter]");
  dropdowns.forEach(function (dropdown) {
    var table = document.querySelector(dropdown.dataset.statusFilter);
    table.filters = table.filters || {};
    dropdown.addEventListener("change", function () {
      table.filters.status = dropdown.value;
      SF.applyFilters(table);
    });
  });

  // On/off switches such
  var switches = document.querySelectorAll("[data-status-toggle]");
  switches.forEach(function (checkbox) {
    var table = document.querySelector(checkbox.dataset.statusToggle);
    table.filters = table.filters || {};
    checkbox.addEventListener("change", function () {
      table.filters.only = checkbox.checked ? checkbox.dataset.statusValue : "";
      SF.applyFilters(table);
    });
  });
}


// Sorting

// Get the value to sort a cell by.
function getSortValue(row, columnIndex, kind) {
  var cell = row.children[columnIndex];
  var text = cell.dataset.sortValue !== undefined ? cell.dataset.sortValue : cell.textContent.trim();
  if (kind === "num") {
    return parseFloat(text) || 0;
  }
  return text.toLowerCase();
}

function setUpSorting() {
  var tables = document.querySelectorAll("table.sortable");
  tables.forEach(function (table) {
    var headings = table.querySelectorAll("thead th[data-sort]");

    headings.forEach(function (heading) {
      heading.querySelector("button").addEventListener("click", function () {
        var columnIndex = Array.prototype.indexOf.call(heading.parentNode.children, heading);
        var kind = heading.dataset.sort;

        // Click once = ascending, click again = descending.
        var direction = heading.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
        headings.forEach(function (h) { h.setAttribute("aria-sort", "none"); });
        heading.setAttribute("aria-sort", direction);

        var body = table.tBodies[0];
        var emptyRow = body.querySelector(".sf-empty-row");
        var rows = Array.from(body.querySelectorAll("tr:not(.sf-empty-row)"));

        rows.sort(function (a, b) {
          var x = getSortValue(a, columnIndex, kind);
          var y = getSortValue(b, columnIndex, kind);
          var result = 0;
          if (x < y) { result = -1; }
          if (x > y) { result = 1; }
          return direction === "ascending" ? result : -result;
        });

        // Put the rows back in the new order.
        rows.forEach(function (row) { body.insertBefore(row, emptyRow); });
      });
    });
  });
}


// The job pop-up

function setUpJobPopup() {
  var popupElement = document.getElementById("jobModal");
  if (!popupElement) {
    return;
  }
  var popup = bootstrap.Modal.getOrCreateInstance(popupElement);
  var alertButton = document.getElementById("jobModalAlertBtn");
  var openJobId = null;

  // Fill the pop-up with one job's details
  SF.openJob = function (jobId) {
    var job = SF.jobs[jobId];
    if (!job) {
      return;
    }
    openJobId = jobId;

    document.getElementById("jobModalTitle").textContent = jobId + " · " + job.customer;
    document.getElementById("jobModalMeta").replaceChildren(
      job.description + " · starts " + job.start + " ", SF.badge(job.status));

    var tableBody = document.getElementById("jobModalLines");
    tableBody.replaceChildren();
    var anyShort = false;

    job.lines.forEach(function (line) {
      var isShort = line.short_by > 0;
      if (isShort) {
        anyShort = true;
      }

      var checkText = "OK";
      var checkClass = "text-success";
      if (line.free === null) {
        checkText = "—";
        checkClass = "text-body-secondary";
      } else if (isShort) {
        checkText = "Short by " + line.short_by;
        checkClass = "text-danger fw-semibold";
      }

      tableBody.append(SF.el("tr", {}, [
        SF.el("td", { class: "fw-semibold", text: line.sku }),
        SF.el("td", { text: line.desc }),
        SF.el("td", { class: "text-end", text: line.qty }),
        SF.el("td", { class: "text-end", text: line.free === null ? "—" : line.free }),
        SF.el("td", { class: checkClass, text: checkText })
      ]));
    });

    // Only show the "Alert purchasing" button when something is short.
    alertButton.classList.toggle("d-none", !anyShort);
    alertButton.disabled = false;
    popup.show();
  };

  alertButton.addEventListener("click", function () {
    alertButton.disabled = true;
    SF.toast("Shortage alert sent to purchasing for " + openJobId + " (demo).");
  });

  // Any button with data-job-detail opens that job.
  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-job-detail]");
    if (button) {
      SF.openJob(button.dataset.jobDetail);
    }
  });
}


document.addEventListener("DOMContentLoaded", function () {
  setUpFilters();
  setUpSorting();
  setUpJobPopup();
});