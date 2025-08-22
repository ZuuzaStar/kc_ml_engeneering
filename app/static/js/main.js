// Utility functions
function setCreds(e, p) {
  try {
    localStorage.setItem('email', e);
    localStorage.setItem('password', p);
  } catch (_) {}
}

function getCreds() {
  try {
    return {
      email: localStorage.getItem('email') || document.getElementById('email').value,
      password: localStorage.getItem('password') || document.getElementById('password').value
    };
  } catch (_) {
    return {
      email: document.getElementById('email').value,
      password: document.getElementById('password').value
    };
  }
}

function authHeader() {
  const c = getCreds();
  if (!c.email || !c.password) return {};
  return {'Authorization': 'Basic ' + btoa(c.email + ':' + c.password)};
}

function setText(id, t) {
  document.getElementById(id).textContent = t;
}

function setHTML(id, h) {
  document.getElementById(id).innerHTML = h;
}

// Auth status management
function showAuthStatus(email) {
  var a = document.getElementById('auth_inputs');
  var b = document.getElementById('auth_status');
  if (a && b) {
    document.getElementById('me_email').textContent = email;
    a.classList.add('hidden');
    b.classList.remove('hidden');
  }
  
  var e = document.getElementById('email');
  var p = document.getElementById('password');
  if (e) e.value = '';
  if (p) p.value = '';
  
  var phl = document.getElementById('prediction_history_link');
  var thl = document.getElementById('transaction_history_link');
  if (phl) phl.classList.remove('hidden');
  if (thl) thl.classList.remove('hidden');
  
  var rb = document.getElementById('req_btn');
  if (rb) rb.disabled = false;
  
  var bc = document.getElementById('balance_card');
  if (bc) bc.classList.remove('hidden');
  
  var at = document.getElementById('auth_title');
  if (at) at.textContent = 'Profile';
  
  // Очищаем сообщения об ошибках при успешной авторизации
  setText('pred_error', '');
  setText('balance_error', '');
  setText('auth_msg', '');
}

function showAuthInputs() {
  var a = document.getElementById('auth_inputs');
  var b = document.getElementById('auth_status');
  if (a && b) {
    a.classList.remove('hidden');
    b.classList.add('hidden');
  }
  var at = document.getElementById('auth_title');
  if (at) at.textContent = 'Authorisation';
  
  // Очищаем все сообщения и поля при разлогине
  setText('pred_error', '');
  setText('balance_error', '');
  setText('auth_msg', '');
  setHTML('pred_list', '');
  setText('balance', '—');
  
  // Очищаем поля ввода
  var prompt = document.getElementById('prompt');
  if (prompt) prompt.value = '';
  
  var topup = document.getElementById('topup');
  if (topup) topup.value = '';
}

// Auth functions
async function signup() {
  const e = document.getElementById('email').value,
        p = document.getElementById('password').value;
  if (!e || !p) return setText('auth_msg', 'Enter email & password');
  
  const r = await fetch('/api/users/signup', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: e, password: p})
  });
  
  setCreds(e, p);
  setText('auth_msg', r.ok ? 'Signed up' : 'Signup failed');
  if (r.ok) {
    showAuthStatus(e);
    getBalance();
  } else {
    // Очищаем другие сообщения при неудачной попытке
    setText('pred_error', '');
    setText('balance_error', '');
  }
}

async function signin() {
  const e = document.getElementById('email').value,
        p = document.getElementById('password').value;
  if (!e || !p) return setText('auth_msg', 'Enter email & password');
  
  const r = await fetch('/api/users/signin', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: e, password: p})
  });
  
  setCreds(e, p);
  setText('auth_msg', r.ok ? 'Signed in' : 'Signin failed');
  if (r.ok) {
    showAuthStatus(e);
    getBalance();
  } else {
    // Очищаем другие сообщения при неудачной попытке
    setText('pred_error', '');
    setText('balance_error', '');
  }
}

// Balance functions
async function getBalance() {
  setText('balance_error', '');
  const r = await fetch('/api/users/balance', {headers: authHeader()});
  if (!r.ok) return setText('balance_error', 'Unable to fetch balance');
  
  try {
    const d = await r.json();
    setText('balance', (d['Current balance'] ?? '—'));
    // Очищаем сообщения об ошибках при успешном получении баланса
    setText('balance_error', '');
  } catch (e) {
    setText('balance_error', 'Error parsing response');
  }
}

async function topUp() {
  setText('balance_error', '');
  const a = parseFloat(document.getElementById('topup').value || '0');
  const {email} = getCreds();
  if (!email || !a) return setText('balance_error', 'Enter amount & be logged in');
  
  const r = await fetch('/api/users/balance/adjust', {
    method: 'POST',
    headers: {...authHeader(), 'Content-Type': 'application/json'},
    body: JSON.stringify({email: email, amount: a})
  });
  
  if (!r.ok) return setText('balance_error', 'Top up failed');
  
  // Очищаем поле ввода после успешного пополнения
  document.getElementById('topup').value = '';
  setText('balance_error', ''); // Очищаем сообщение об ошибке
  getBalance();
}

// Movie rendering
function renderMovies(list) {
  if (!Array.isArray(list) || list.length === 0) {
    return '<div class="muted">No recommendations yet</div>';
  }
  
  return list.map(m => `
    <div class="movie">
      <div><strong>${m.title ?? '-'} (${m.year ?? '-'})</strong></div>
      <div class="muted">${(m.description ?? '').slice(0, 320)}</div>
      <div>${(m.genres || []).map(g => `<span class="tag">${g}</span>`).join('')}</div>
    </div>
  `).join('');
}

// Prediction functions
async function newPrediction() {
  setText('pred_error', '');
  document.getElementById('pred_error').className = 'error';
  
  const msg = document.getElementById('prompt').value.trim();
  if (!msg) return setText('pred_error', 'Enter your request');
  
  setText('pred_error', 'Processing...');
  document.getElementById('pred_error').className = 'info'; // Меняем класс на info для "Processing..."
  
  try {
    const r = await fetch(`/api/events/prediction/new?message=${encodeURIComponent(msg)}&top=10`, {
      method: 'POST',
      headers: authHeader()
    });
    
    if (!r.ok) {
      let err = '';
      try {
        const errData = await r.json();
        // Если ошибка в формате JSON, извлекаем сообщение
        err = errData.detail || errData.message || JSON.stringify(errData);
      } catch {
        // Если не JSON, читаем как текст
        err = await r.text();
      }
      
      if (r.status === 401) {
        openAuthModal('Session expired. Please sign in again');
        return;
      }
      
      if (r.status === 402) {
        // Ошибка недостатка средств - показываем понятное сообщение
        let insufficientFundsMsg = 'Insufficient funds';
        try {
          // Пытаемся распарсить JSON для извлечения деталей
          const errData = JSON.parse(err);
          if (errData.detail) {
            // Извлекаем информацию о балансе и требуемой сумме
            const detail = errData.detail;
            if (detail.includes('Баланс:') && detail.includes('требуется:')) {
              // Показываем понятное сообщение на русском
              insufficientFundsMsg = 'Недостаточно средств для предсказания';
            } else {
              insufficientFundsMsg = detail;
            }
          }
        } catch {
          // Если не удалось распарсить JSON, используем исходный текст
          insufficientFundsMsg = err;
        }
        
        setText('pred_error', insufficientFundsMsg);
        document.getElementById('pred_error').className = 'error';
        // Обновляем баланс, чтобы показать актуальное состояние
        getBalance();
        return;
      }
      
      document.getElementById('pred_error').className = 'error';
      return setText('pred_error', `Error: ${err}`);
    }
    
    const data = await r.json();
    if (data.length === 0) {
      document.getElementById('pred_error').className = 'error';
      return setText('pred_error', 'No recommendations found');
    }
    
    setHTML('pred_list', renderMovies(data));
    setText('pred_error', 'Recommendations ready!');
    document.getElementById('pred_error').className = 'success';
    
    // Очищаем поле ввода промпта
    document.getElementById('prompt').value = '';
    
    // Обновляем баланс после успешного предсказания
    getBalance();
  } catch (e) {
    document.getElementById('pred_error').className = 'error';
    setText('pred_error', `Error: ${e.message}`);
  }
}

// Logout function
function logout() {
  try {
    localStorage.removeItem('email');
    localStorage.removeItem('password');
  } catch (_) {}
  
  showAuthInputs();
  setText('balance', '—');
  setHTML('pred_list', '');
  setText('pred_error', ''); // Очищаем сообщение о рекомендациях
  setText('auth_msg', 'Logged out');
  
  var phl = document.getElementById('prediction_history_link');
  if (phl) phl.classList.add('hidden');
  
  var thl = document.getElementById('transaction_history_link');
  if (thl) thl.classList.add('hidden');
  
  var rb = document.getElementById('req_btn');
  if (rb) rb.disabled = true;
  
  var bc = document.getElementById('balance_card');
  if (bc) bc.classList.add('hidden');
}

// Modal auth
function openAuthModal(message) {
  var ex = document.getElementById('auth_modal');
  if (ex) {ex.remove();}
  
  var modal = document.createElement('div');
  modal.id = 'auth_modal';
  modal.className = 'modal';
  modal.innerHTML = `
    <div class='modal-card'>
      <h3 class='title'>Auth</h3>
      <div class='muted' style='margin-bottom:8px;'>${message || ''}</div>
      <div class='stack'>
        <input id='m_email' class='input' type='email' placeholder='Email'/>
        <input id='m_password' class='input' type='password' placeholder='Password'/>
        <div class='row'>
          <button class='btn primary' id='m_signin'>Sign in</button>
          <button class='btn' id='m_cancel'>Cancel</button>
        </div>
        <div id='m_msg' class='error'></div>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  document.getElementById('m_cancel').onclick = function() {
    document.body.removeChild(modal);
  };
  
  document.getElementById('m_signin').onclick = async function() {
    var e = document.getElementById('m_email').value;
    var p = document.getElementById('m_password').value;
    
    if (!e || !p) {
      document.getElementById('m_msg').textContent = 'Enter email & password';
      return;
    }
    
    const r = await fetch('/api/users/signin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: e, password: p})
    });
    
    if (!r.ok) {
      document.getElementById('m_msg').textContent = 'Signin failed';
      return;
    }
    
    setCreds(e, p);
    showAuthStatus(e);
    getBalance();
    document.body.removeChild(modal);
    
    // Очищаем сообщения об ошибках после успешной авторизации
    setText('pred_error', '');
    setText('balance_error', '');
  };
}

// Initialize on page load
function init() {
  let e = '', p = '';
  try {
    e = localStorage.getItem('email') || '';
    p = localStorage.getItem('password') || '';
  } catch (_) {
    e = '';
    p = '';
  }
  
  if (e && p) {
    showAuthStatus(e);
    getBalance();
    var bc = document.getElementById('balance_card');
    if (bc) bc.classList.remove('hidden');
  } else {
    // Если пользователь не авторизован, очищаем все сообщения
    setText('pred_error', '');
    setText('balance_error', '');
    setText('auth_msg', '');
    setHTML('pred_list', '');
    setText('balance', '—');
  }
}

// Export functions for global use
window.setCreds = setCreds;
window.getCreds = getCreds;
window.authHeader = authHeader;
window.setText = setText;
window.setHTML = setHTML;
window.showAuthStatus = showAuthStatus;
window.showAuthInputs = showAuthInputs;
window.signup = signup;
window.signin = signin;
window.getBalance = getBalance;
window.topUp = topUp;
window.renderMovies = renderMovies;
window.newPrediction = newPrediction;
window.logout = logout;
window.openAuthModal = openAuthModal;
window.init = init;
