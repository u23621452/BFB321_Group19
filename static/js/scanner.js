/* Shop-floor scanner page (demo).
   The camera scan is pretend: it suggests the next item on the job's
   materials list that still has to be picked. A real version would read
   the barcode with the phone camera and send each pick to the server. This will be done in the backend. */

var jobSelect = document.getElementById("scanJob");
var pickPanel = document.getElementById("pickPanel");
var quantityBox = document.getElementById("pickQty");

var picked = {};          // what has been picked so far
var currentSku = null;    // the item shown in the pick panel right now
var scanCount = 0;        // used to move through the list on each scan


// Helper functions

function currentJob() {
  return SF.jobs[jobSelect.value];
}

// How many of this item have been picked for the selected job.
function pickedSoFar(sku) {
  var forJob = picked[jobSelect.value] || {};
  return forJob[sku] || 0;
}

// The job's materials line for this item or undefined if it is not on the list.
function findLine(sku) {
  var lines = currentJob().lines;
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].sku === sku) {
      return lines[i];
    }
  }
  return undefined;
}

// How many of this item the job still needs.
function stillNeeded(sku) {
  var line = findLine(sku);
  if (!line) {
    return 0;
  }
  return Math.max(line.qty - pickedSoFar(sku), 0);
}


// The pick panel

function showPickPanel(sku) {
  currentSku = sku;
  var item = SF.stock[sku];

  document.getElementById("pickTitle").textContent = sku;
  document.getElementById("pickDesc").textContent = item.desc;
  document.getElementById("pickBin").textContent = "Bin " + item.bin;

  var note = document.getElementById("pickNeed");
  var line = findLine(sku);

  if (line) {
    var remaining = stillNeeded(sku);
    note.className = "alert alert-info py-2 mt-3 mb-3";
    note.textContent = "Needed for " + jobSelect.value + ": " + line.qty +
                       " · picked " + pickedSoFar(sku) + " · remaining " + remaining;
    quantityBox.value = Math.max(Math.min(remaining, item.available), 1);
  } else {
    note.className = "alert alert-warning py-2 mt-3 mb-3";
    note.textContent = "This item is not on the materials list for " + jobSelect.value +
                       ". Check with the storeroom before picking.";
    quantityBox.value = 1;
  }

  pickPanel.classList.remove("d-none");
  quantityBox.focus();
}

function hidePickPanel() {
  pickPanel.classList.add("d-none");
  currentSku = null;
}


// Scanning

// Fake camera scan(For now, will be real in backend): suggest an item that still needs picking.
document.getElementById("scanBtn").addEventListener("click", function () {
  var stillToPick = currentJob().lines.filter(function (line) {
    return stillNeeded(line.sku) > 0;
  });

  if (stillToPick.length === 0) {
    SF.toast("Everything for " + jobSelect.value + " has been picked.");
    return;
  }

  showPickPanel(stillToPick[scanCount % stillToPick.length].sku);
  scanCount++;
});

// Typing a code by hand.
var manualForm = document.getElementById("manualForm");
var codeBox = document.getElementById("manualCode");

manualForm.addEventListener("submit", function (event) {
  event.preventDefault();
  var code = codeBox.value.trim().toUpperCase();

  // Unknown codes are marked invalid, which shows the red message.
  codeBox.setCustomValidity(SF.stock[code] ? "" : "unknown");
  manualForm.classList.add("was-validated");

  if (!manualForm.checkValidity()) {
    codeBox.focus();
    return;
  }

  manualForm.classList.remove("was-validated");
  codeBox.value = "";
  showPickPanel(code);
});

// Clear the red message as soon as the user types again.
codeBox.addEventListener("input", function () {
  codeBox.setCustomValidity("");
});


// Quantity and confirming

document.getElementById("qtyMinus").addEventListener("click", function () {
  quantityBox.value = Math.max((parseInt(quantityBox.value, 10) || 1) - 1, 1);
});

document.getElementById("qtyPlus").addEventListener("click", function () {
  quantityBox.value = (parseInt(quantityBox.value, 10) || 0) + 1;
});

document.getElementById("confirmPick").addEventListener("click", function () {
  var amount = parseInt(quantityBox.value, 10);
  var item = SF.stock[currentSku];

  if (!Number.isInteger(amount) || amount < 1) {
    SF.toast("Enter a quantity of 1 or more.");
    quantityBox.focus();
    return;
  }
  if (amount > item.onHand) {
    SF.toast("Only " + item.onHand + " " + item.unit + " on hand for " + currentSku + ".");
    quantityBox.focus();
    return;
  }

  // Remember the pick.
  if (!picked[jobSelect.value]) {
    picked[jobSelect.value] = {};
  }
  picked[jobSelect.value][currentSku] = pickedSoFar(currentSku) + amount;

  // Add it to the "Picked this session" list.
  var time = new Date().toLocaleTimeString("en-ZA", { hour: "2-digit", minute: "2-digit" });
  var listItem = SF.el("li", { class: "list-group-item d-flex justify-content-between align-items-center" }, [
    SF.el("div", {}, [
      SF.el("span", { class: "fw-semibold", text: currentSku }),
      SF.el("div", { class: "small text-body-secondary", text: jobSelect.value + " · " + time })
    ]),
    SF.el("span", { class: "badge text-bg-success", text: "+" + amount + " " + item.unit })
  ]);

  var emptyMessage = document.getElementById("histEmpty");
  if (emptyMessage) {
    emptyMessage.remove();
  }
  document.getElementById("pickHistory").prepend(listItem);

  SF.toast("Ledger updated: " + amount + " × " + currentSku + " issued to " + jobSelect.value + " (demo).");
  hidePickPanel();
});

document.getElementById("cancelPick").addEventListener("click", hidePickPanel);

// Switching to another work order starts the scan list again.
jobSelect.addEventListener("change", function () {
  hidePickPanel();
  scanCount = 0;
});


// Requesting extra material

var requestForm = document.getElementById("requestForm");

requestForm.addEventListener("submit", function (event) {
  event.preventDefault();
  requestForm.classList.add("was-validated");

  if (!requestForm.checkValidity()) {
    return;
  }

  SF.toast("Request for " + document.getElementById("reqQty").value + " × " +
           document.getElementById("reqSku").value + " sent to the storeroom queue (demo).");
  bootstrap.Modal.getInstance(document.getElementById("requestModal")).hide();
  requestForm.reset();
  requestForm.classList.remove("was-validated");
});