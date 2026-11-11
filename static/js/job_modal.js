/* The job detail pop-up. Any button with data-job-detail="J-2026-0431"
   opens it, and the details are loaded from the API. */
(function () {
  'use strict';
  var el = SF.el;

  var modalElement = document.getElementById('jobModal');
  if (!modalElement) { return; }
  var modal = bootstrap.Modal.getOrCreateInstance(modalElement);
  var title = document.getElementById('jobModalTitle');
  var meta = document.getElementById('jobModalMeta');
  var linesBody = document.getElementById('jobModalLines');

  function stockCheck(job, line) {
    if (job.status === 'issued') {
      return el('span', { class: 'text-success', text: 'Issued' });
    }
    if (line.short_by > 0) {
      return el('span', { class: 'text-danger fw-semibold', text: 'Short by ' + line.short_by });
    }
    return el('span', { class: 'text-success', text: 'OK' });
  }

  SF.openJob = async function (jobNumber) {
    title.textContent = jobNumber;
    meta.textContent = '';
    SF.showLoading(linesBody, 5);
    modal.show();

    try {
      var job = await SF.api('GET', '/api/jobs/' + encodeURIComponent(jobNumber));
      title.textContent = job.job_number + ' · ' + job.customer;
      meta.replaceChildren(
        job.description + ' · starts ' + SF.formatDate(job.start_date) + ' · ' + job.priority + ' priority ',
        SF.badge(job.status));
      linesBody.replaceChildren(...job.lines.map(function (line) {
        return el('tr', {}, [
          el('td', { class: 'fw-semibold', text: line.sku }),
          el('td', { text: line.description }),
          el('td', { class: 'text-end', text: line.qty }),
          el('td', { class: 'text-end', text: line.picked_qty }),
          el('td', {}, [stockCheck(job, line)])
        ]);
      }));
    } catch (problem) {
      SF.showError(linesBody, 5, 'Could not load this job: ' + problem.message,
        function () { SF.openJob(jobNumber); });
    }
  };

  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-job-detail]');
    if (button) { SF.openJob(button.dataset.jobDetail); }
  });
})();