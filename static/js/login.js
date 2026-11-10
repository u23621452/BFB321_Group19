/* Login page: sends the email and password to the API. */
(function () {
  'use strict';

  var form = document.getElementById('loginForm');
  var button = document.getElementById('loginBtn');
  var errorBox = document.getElementById('loginError');

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    errorBox.classList.add('d-none');

    var email = document.getElementById('email').value.trim();
    var password = document.getElementById('password').value;
    if (!email || !password) {
      errorBox.textContent = 'Enter your email and password.';
      errorBox.classList.remove('d-none');
      return;
    }

    button.disabled = true;
    button.textContent = 'Logging in…';
    try {
      await SF.api('POST', '/api/auth/login', { email: email, password: password });
      location.href = '/dashboard';
    } catch (problem) {
      errorBox.textContent = problem.message;
      errorBox.classList.remove('d-none');
      button.disabled = false;
      button.textContent = 'Log in';
    }
  });
})();