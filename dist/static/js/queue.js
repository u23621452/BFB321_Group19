/* Storeroom queue page: the "Next 7 days" / "Next 14 days" buttons. */

var queueTable = document.getElementById("queueTable");
var countLabel = document.getElementById("queueCount");

queueTable.filters = queueTable.filters || {};

// Only show jobs that start within the chosen number of days.
function setWindow(days) {
  queueTable.filters.days = days;
  SF.applyFilters(queueTable);
}

// app.js announces how many rows are showing after every filter change.
queueTable.addEventListener("sf:filtered", function (event) {
  var count = event.detail.visible;
  countLabel.textContent = count + (count === 1 ? " job" : " jobs") + " shown";
});

// The two buttons are radio inputs named "window" (values 7 and 14).
var buttons = document.querySelectorAll('input[name="window"]');
buttons.forEach(function (button) {
  button.addEventListener("change", function () {
    setWindow(Number(button.value));
  });
});

setWindow(7);   // start with the 7-day view