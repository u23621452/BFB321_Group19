/* The New job file form on the Job files page does the following,
   - add and remove materials lines
   - check the fields and show messages
   - check whether the stock covers the job

   The preview repeats the logic of models/stock_model.py in JavaScript so
   the demo works without a server. */

var form = document.getElementById("jobForm");
var linesBox = document.getElementById("bomLines");
var bomError = document.getElementById("bomError");
var resultBox = document.getElementById("reserveResult");
var jobTable = document.getElementById("jobTable");
var lineCounter = 0;


// Materials lines 

// Add one blank line
function addLine() {
  lineCounter++;
  var n = lineCounter;

  var select = SF.el("select", { class: "form-select", id: "sku" + n, required: "" });
  select.append(SF.el("option", { value: "", text: "Choose SKU…", disabled: "", selected: "" }));
  for (var sku in SF.stock) {
    select.append(SF.el("option", { value: sku, text: sku + " – " + SF.stock[sku].desc }));
  }

  var quantity = SF.el("input", {
    type: "number", class: "form-control", id: "qty" + n,
    min: "1", step: "1", required: "", inputmode: "numeric", placeholder: "Qty"
  });

  var deleteButton = SF.el("button", {
    type: "button", class: "btn btn-outline-danger", "aria-label": "Remove line " + n
  });
  deleteButton.append(SF.el("i", { class: "bi bi-trash", "aria-hidden": "true" }));

  var row = SF.el("div", { class: "sf-bom-row" }, [
    SF.el("div", {}, [
      SF.el("label", { for: "sku" + n, class: "visually-hidden", text: "Item for line " + n }),
      select,
      SF.el("div", { class: "invalid-feedback", text: "Choose an item (each item only once)." })
    ]),
    SF.el("div", {}, [
      SF.el("label", { for: "qty" + n, class: "visually-hidden", text: "Quantity for line " + n }),
      quantity,
      SF.el("div", { class: "invalid-feedback", text: "Whole number, 1 or more." })
    ]),
    deleteButton
  ]);

  deleteButton.addEventListener("click", function () {
    row.remove();
  });
  linesBox.append(row);
}

// Read all the lines into a list
function readLines() {
  var rows = linesBox.querySelectorAll(".sf-bom-row");
  var lines = [];
  for (var i = 0; i < rows.length; i++) {
    var select = rows[i].querySelector("select");
    var input = rows[i].querySelector("input");
    lines.push({ sku: select.value, qty: parseInt(input.value, 10), select: select });
  }
  return lines;
}


// Checking the form

// Returns true when everything is filled in correctly.
function formIsValid() {
  var lines = readLines();

  // Make sure the same item does not appear twice.
  var seen = {};
  lines.forEach(function (line) {
    var isDuplicate = line.sku !== "" && seen[line.sku] === true;
    line.select.setCustomValidity(isDuplicate ? "duplicate" : "");
    seen[line.sku] = true;
  });

  // Make sure start date is not in the past.
  var startDate = document.getElementById("startDate");
  var isPast = startDate.value !== "" && startDate.value < SF.today;
  startDate.setCustomValidity(isPast ? "past" : "");

  // At least one materials line is needed.
  var noLines = lines.length === 0;
  bomError.classList.toggle("d-none", !noLines);
  bomError.classList.toggle("d-block", noLines);

  return form.checkValidity() && !noLines;
}

// Work out the next job number.
function nextJobId() {
  var highest = 0;
  for (var id in SF.jobs) {
    var number = parseInt(id.split("-")[2], 10);
    if (number > highest) {
      highest = number;
    }
  }
  return "J-2026-" + String(highest + 1).padStart(4, "0");
}


// Saving the job (demo only)

form.addEventListener("submit", function (event) {
  event.preventDefault();               // stop the page reloading
  form.classList.add("was-validated");  // show the red/green field marks

  if (!formIsValid()) {
    var firstProblem = form.querySelector(":invalid");
    if (firstProblem) {
      firstProblem.focus();
    }
    return;
  }

  // Stock check
  var lines = readLines().map(function (line) {
    var free = SF.stock[line.sku].available;
    return {
      sku: line.sku,
      desc: SF.stock[line.sku].desc,
      qty: line.qty,
      free: free,
      short_by: Math.max(line.qty - free, 0)
    };
  });

  var shortLines = lines.filter(function (line) { return line.short_by > 0; });
  var status = shortLines.length > 0 ? "shortage" : "reserved";

  var jobId = nextJobId();
  var customer = document.getElementById("customer").value.trim();
  var description = document.getElementById("description").value.trim();
  var startDate = document.getElementById("startDate").value;

  // Remember the job so the pop-up can show it.
  SF.jobs[jobId] = {
    customer: customer, description: description, start: startDate,
    status: status, lines: lines
  };

  // Reserve the stock
  lines.forEach(function (line) {
    SF.stock[line.sku].available = Math.max(line.free - line.qty, 0);
  });

  // Add a new row at the top of the job table.
  var shortDate = new Date(startDate + "T00:00").toLocaleDateString("en-ZA", { day: "numeric", month: "short" });
  var newRow = SF.el("tr", { "data-status": status }, [
    SF.el("td", { class: "fw-semibold", text: jobId }),
    SF.el("td", {}, [customer, SF.el("div", { class: "small text-body-secondary", text: description })]),
    SF.el("td", { "data-sort-value": startDate, text: shortDate }),
    SF.el("td", { "data-sort-value": status }, [SF.badge(status)]),
    SF.el("td", { class: "text-end" }, [
      SF.el("button", { type: "button", class: "btn btn-sm btn-outline-primary", "data-job-detail": jobId, text: "View" })
    ])
  ]);
  jobTable.tBodies[0].prepend(newRow);
  SF.applyFilters(jobTable);

  // Tell the user what happened.
  var message;
  if (shortLines.length > 0) {
    var names = shortLines.map(function (l) { return l.sku + " (short by " + l.short_by + ")"; });
    message = "Stock reserved, but " + shortLines.length + " line(s) are short: " + names.join(", ") +
              ". Purchasing can be alerted from the job detail.";
  } else {
    message = "All lines are covered by free stock and are now reserved.";
  }
  var box = SF.el("div", {
    class: "alert alert-" + (shortLines.length > 0 ? "warning" : "success") + " mb-0",
    role: "status"
  });
  box.append(SF.el("strong", { text: jobId + " created. " }), message);

  form.reset();                       // clears the form (see the reset handler below)
  resultBox.replaceChildren(box);
  SF.toast(jobId + " captured (demo - not saved to a server).");
});

// When the form is cleared, go back to one blank material line.
form.addEventListener("reset", function () {
  form.classList.remove("was-validated");
  resultBox.replaceChildren();
  setTimeout(function () {
    linesBox.replaceChildren();
    addLine();
  });
});

document.getElementById("addBomLine").addEventListener("click", addLine);

// After a failed submit, re-check while the user fixes things.
form.addEventListener("input", function () {
  if (form.classList.contains("was-validated")) {
    formIsValid();
  }
});

addLine();   // start with one blank line