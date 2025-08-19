from fastapi import APIRouter
from fastapi.responses import HTMLResponse

web_ui = APIRouter()

BASE_CSS = """
  :root { --bg:#0b1220; --card:#121a2b; --muted:#7c92b2; --text:#e6edf7; --accent:#4f7cff; --accent-2:#2bd4a5; --danger:#ff5d5d; --border:#1f2a44; }
  *{box-sizing:border-box}
  html, body { height: 100%; }
  body{margin:0;padding:24px;min-height:100vh;font-family:ui-sans-serif,system-ui,-apple-system,Roboto;background:radial-gradient(1200px 800px at 20% -10%,#17233a 0%,transparent 50%),radial-gradient(1000px 600px at 110% 10%,#0f1a30 0%,transparent 40%),var(--bg);color:var(--text)}
  a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}
  .container{width:100%;max-width:1200px;margin:0 auto;min-height:calc(100vh - 48px)}
  .grid{display:grid;grid-template-columns:1fr;gap:16px} @media(min-width:900px){.grid{grid-template-columns:360px 1fr}}
  .card{background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.01));border:1px solid var(--border);border-radius:14px;padding:16px;backdrop-filter:blur(6px);box-shadow:0 6px 20px rgba(0,0,0,.25)}
  .title{font-size:22px;margin:0 0 8px;letter-spacing:.3px}
  .muted{color:var(--muted);font-size:14px}
  .row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
  .input{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:10px;background:#0e1526;color:var(--text)}
  .btn{padding:10px 14px;border-radius:10px;border:1px solid var(--border);background:#0f172a;color:var(--text);cursor:pointer}
  .btn.primary{background:linear-gradient(90deg,var(--accent),#7a9aff);border:none;color:#fff}
  .btn.success{background:linear-gradient(90deg,var(--accent-2),#35e3b3);border:none;color:#07271e}
  .btn[disabled]{opacity:.45; cursor:not-allowed; filter: grayscale(35%);}
  .stack{display:flex;flex-direction:column;gap:10px}
  .scroll{height:420px;overflow:auto;border:1px solid var(--border);border-radius:12px;padding:10px;background:#0c1426}
  .movie{display:grid;grid-template-columns:1fr;gap:6px;padding:12px;border-bottom:1px dashed var(--border)} .movie:last-child{border-bottom:0}
  .tag{display:inline-block;padding:2px 8px;font-size:12px;border-radius:999px;background:#0d1b36;border:1px solid var(--border);color:var(--muted);margin-right:6px}
  .topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
  .link{color:var(--muted)} .error{color:var(--danger);font-size:13px;min-height:18px}
  .hidden{display:none}
  /* Modal */
  .modal{position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:50}
  .modal-card{width:100%;max-width:420px;background:#0e1526;border:1px solid var(--border);border-radius:14px;padding:16px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
"""

@web_ui.get("/web", response_class=HTMLResponse)
async def web_index():
    html = """
<!DOCTYPE html><html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Movie Recommender</title>""" + "<style>" + BASE_CSS + "</style>" + """</head>
<body><div class='container'>
  <div class='topbar'>
    <div class='row' style='gap:12px;'><strong>Movie Recommender</strong><span class='muted'>Demo</span></div>
    <div class='row' style='gap:12px;'>
      <a id='prediction_history_link' class='link hidden' href='/web/prediction-history'>Prediction History →</a>
      <a id='transaction_history_link' class='link hidden' href='/web/transaction-history'>Transaction History →</a>
    </div>
  </div>
  <div class='grid'>
    <div class='stack'>
      <div class='card'>
        <h3 class='title' id='auth_title'>Authorisation</h3>
        <div class='stack'>
          <div id='auth_inputs'>
            <div class='stack'>
              <input id='email' class='input' type='email' placeholder='Email'/>
              <input id='password' class='input' type='password' placeholder='Password'/>
              <div class='row'>
                <button class='btn primary' onclick='signup()'>Sign up</button>
                <button class='btn' onclick='signin()'>Sign in</button>
                <span id='auth_msg' class='muted'></span>
              </div>
            </div>
          </div>
          <div id='auth_status' class='row hidden' style='justify-content:space-between;'>
            <div class='row' style='gap:8px;'>
              <span class='muted'>Signed in as</span>
              <strong id='me_email'></strong>
            </div>
            <button class='btn' onclick='logout()'>Logout</button>
          </div>
        </div>
      </div>
      <div id='balance_card' class='card hidden'>
        <h3 class='title'>Balance</h3>
        <div class='stack'>
          <div class='row'>
            <input id='topup' class='input' type='number' min='1' step='1' placeholder='Top up amount' style='max-width:220px;'/>
          </div>
          <div class='row' style='align-items:center;'>
            <div class='row' style='gap:8px;'>
              <button class='btn success' onclick='topUp()'>Top up</button>
              <button class='btn' onclick='getBalance()'>Refresh</button>
            </div>
            <strong id='balance' style='font-size:18px; margin-left:auto;'>—</strong>
          </div>
          <div id='balance_error' class='error'></div>
        </div>
      </div>
    </div>
    <div class='card'>
      <h3 class='title'>Recommendations</h3>
      <div class='stack'>
        <div class='row' style='gap:8px; align-items:center;'>
          <input id='prompt' class='input' type='text' placeholder='What would you like to watch?' style='flex:1;'/>
          <button id='req_btn' class='btn primary' onclick='newPrediction()' disabled>Request</button>
        </div>
        <div id='pred_list' class='scroll' aria-live='polite'></div>
        <div id='pred_error' class='error'></div>
      </div>
    </div>
  </div>
</div>
<script>
function setCreds(e,p){try{localStorage.setItem('email',e);localStorage.setItem('password',p);}catch(_){}}
function getCreds(){try{return {email:localStorage.getItem('email')||document.getElementById('email').value,password:localStorage.getItem('password')||document.getElementById('password').value}}catch(_){return {email:document.getElementById('email').value,password:document.getElementById('password').value}}}
function authHeader(){const c=getCreds(); if(!c.email||!c.password) return {}; return {'Authorization':'Basic '+btoa(c.email+':'+c.password)}}
function setText(id,t){document.getElementById(id).textContent=t}
function setHTML(id,h){document.getElementById(id).innerHTML=h}
function showAuthStatus(email){
  var a=document.getElementById('auth_inputs');
  var b=document.getElementById('auth_status');
  if(a&&b){
    document.getElementById('me_email').textContent=email;
    a.classList.add('hidden');
    b.classList.remove('hidden');
  }
  var e=document.getElementById('email');
  var p=document.getElementById('password');
  if(e) e.value='';
  if(p) p.value='';
  var phl=document.getElementById('prediction_history_link');
  var thl=document.getElementById('transaction_history_link');
  if(phl) phl.classList.remove('hidden');
  if(thl) thl.classList.remove('hidden');
  var rb=document.getElementById('req_btn');
  if(rb) rb.disabled=false;
  var bc=document.getElementById('balance_card');
  if(bc) bc.classList.remove('hidden');
  var at=document.getElementById('auth_title');
  if(at) at.textContent='Profile';
}
function showAuthInputs(){var a=document.getElementById('auth_inputs'); var b=document.getElementById('auth_status'); if(a&&b){a.classList.remove('hidden'); b.classList.add('hidden');} var at=document.getElementById('auth_title'); if(at) at.textContent='Authorisation';}
async function signup(){const e=document.getElementById('email').value,p=document.getElementById('password').value; if(!e||!p) return setText('auth_msg','Enter email & password'); const r=await fetch('/api/users/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})}); setCreds(e,p); setText('auth_msg',r.ok?'Signed up':'Signup failed'); if(r.ok){ showAuthStatus(e); getBalance(); }}
async function signin(){const e=document.getElementById('email').value,p=document.getElementById('password').value; if(!e||!p) return setText('auth_msg','Enter email & password'); const r=await fetch('/api/users/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})}); setCreds(e,p); setText('auth_msg',r.ok?'Signed in':'Signin failed'); if(r.ok){ showAuthStatus(e); getBalance(); }}
async function getBalance(){
    setText('balance_error','');
    const r=await fetch('/api/users/balance',{headers:authHeader()});
    if(!r.ok) return setText('balance_error','Unable to fetch balance');
    try{
        const d=await r.json();
        setText('balance', (d['Current balance']??'—'));
    }catch(e){
        setText('balance_error','Error parsing response');
    }
}
async function topUp(){
    setText('balance_error','');
    const a=parseFloat(document.getElementById('topup').value||'0');
    const {email}=getCreds();
    if(!email||!a) return setText('balance_error','Enter amount & be logged in');
    const r=await fetch('/api/users/balance/adjust',{method:'POST',headers:{...authHeader(),'Content-Type':'application/json'},body:JSON.stringify({email:email,amount:a})});
    if(!r.ok) return setText('balance_error','Top up failed');
    getBalance();
}
function renderMovies(list){if(!Array.isArray(list)||list.length===0) return '<div class="muted">No recommendations yet</div>'; return list.map(m=>`<div class="movie"><div><strong>${m.title??'-'} (${m.year??'-'})</strong></div><div class="muted">${(m.description??'').slice(0,320)}</div><div>${(m.genres||[]).map(g=>`<span class="tag">${g}</span>`).join('')}</div></div>`).join('')}
async function newPrediction(){
    setText('status','');
    const msg=document.getElementById('prompt').value.trim();
    if(!msg) return setText('status','Enter your request');
    setText('status','Processing...');
    try{
        const r=await fetch(`/api/events/prediction/new?message=${encodeURIComponent(msg)}&top=10`,{method:'POST',headers:authHeader()});
        if(!r.ok){
            const err=await r.text();
            if(r.status===401){
                openAuthModal('Session expired. Please sign in again');
                return;
            }
            return setText('status',`Error: ${err}`);
        }
        const data=await r.json();
        if(data.length===0) return setText('status','No recommendations found');
        setHTML('pred_list', renderMovies(data));
        setText('status','Recommendations ready!');
    }catch(e){
        setText('status',`Error: ${e.message}`);
    }
}
(function addLogout(){
  if(!window.logout){
    window.logout = function(){
      try{ localStorage.removeItem('email'); localStorage.removeItem('password'); }catch(_){ }
      showAuthInputs();
      setText('balance','—');
      setHTML('pred_list','');
      setText('auth_msg','Logged out');
      var phl=document.getElementById('prediction_history_link'); if(phl) phl.classList.add('hidden');
      var thl=document.getElementById('transaction_history_link'); if(thl) thl.classList.add('hidden');
      var rb=document.getElementById('req_btn'); if(rb) rb.disabled=true;
      var bc=document.getElementById('balance_card'); if(bc) bc.classList.add('hidden');
    }
  }
})();
(function init(){let e='',p=''; try{e=localStorage.getItem('email')||''; p=localStorage.getItem('password')||'';}catch(_){e='';p='';} if(e&&p){ showAuthStatus(e); getBalance(); var bc=document.getElementById('balance_card'); if(bc) bc.classList.remove('hidden'); }})();
/* Modal auth */
function openAuthModal(message){
  var ex=document.getElementById('auth_modal'); if(ex){ex.remove();}
  var modal=document.createElement('div'); modal.id='auth_modal'; modal.className='modal';
  modal.innerHTML = "<div class='modal-card'><h3 class='title'>Auth</h3><div class='muted' style='margin-bottom:8px;'>"+ (message||'') +"</div>"
    +"<div class='stack'><input id='m_email' class='input' type='email' placeholder='Email'/><input id='m_password' class='input' type='password' placeholder='Password'/>"
    +"<div class='row'><button class='btn primary' id='m_signin'>Sign in</button><button class='btn' id='m_cancel'>Cancel</button></div><div id='m_msg' class='error'></div></div></div>";
  document.body.appendChild(modal);
  document.getElementById('m_cancel').onclick=function(){document.body.removeChild(modal)};
  document.getElementById('m_signin').onclick=async function(){
    var e=document.getElementById('m_email').value; var p=document.getElementById('m_password').value;
    if(!e||!p){document.getElementById('m_msg').textContent='Enter email & password'; return;}
    const r=await fetch('/api/users/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})});
    if(!r.ok){document.getElementById('m_msg').textContent='Signin failed'; return;}
    setCreds(e,p); showAuthStatus(e); getBalance(); document.body.removeChild(modal);
  };
}
</script>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)


@web_ui.get("/web/prediction-history", response_class=HTMLResponse)
async def web_prediction_history():
    html = """
<!DOCTYPE html><html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Prediction History</title>""" + "<style>" + BASE_CSS + "</style>" + """</head>
<body><div class='container'>
  <div class='topbar'><a class='link' href='/web'>← Back</a><strong>Prediction History</strong><span></span></div>
  <div id='protected' class='card hidden'>
    <div class='row' style='justify-content:space-between;'>
      <span id='status' class='muted'></span>
    </div>
    <div style='height:6px'></div>
    <div id='hist' class='scroll'></div>
  </div>
</div>
<script>
function isAuthed(){try{return !!(localStorage.getItem('email')&&localStorage.getItem('password'));}catch(_){return false}}
function authHeader(){try{const e=localStorage.getItem('email'),p=localStorage.getItem('password'); if(!e||!p) return {}; return {'Authorization':'Basic '+btoa(e+':'+p)}}catch(_){return {}}}
function setHTML(id,h){document.getElementById(id).innerHTML=h}
function setText(id,t){document.getElementById(id).textContent=t}
function renderHistory(items){if(!Array.isArray(items)||items.length===0) return '<div class="muted">No prediction history yet</div>'; return items.map(it=>`<div class="movie"><div><strong>${new Date(it.timestamp).toLocaleString()}</strong></div><div class="muted">Prompt: ${it.input_text}</div><div class="muted">Cost: ${it.cost}</div><div>${(it.movies||[]).map(m=>`<span class="tag">${m.title}</span>`).join('')}</div></div>`).join('')}
async function loadHistory(){setText('status',''); const r=await fetch('/api/events/prediction/history',{headers:authHeader()}); if(!r.ok) return setText('status','Failed to load prediction history'); const data=await r.json(); setHTML('hist', renderHistory(data))}
(function init(){if(!isAuthed()){window.location.href='/web'; return;} document.getElementById('protected').classList.remove('hidden'); loadHistory();})();
</script>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)


@web_ui.get("/web/transaction-history", response_class=HTMLResponse)
async def web_transaction_history():
    html = """
<!DOCTYPE html><html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Transaction History</title>""" + "<style>" + BASE_CSS + "</style>" + """</head>
<body><div class='container'>
  <div class='topbar'><a class='link' href='/web'>← Back</a><strong>Transaction History</strong><span></span></div>
  <div id='protected' class='card hidden'>
    <div class='row' style='justify-content:space-between;'>
      <span id='status' class='muted'></span>
    </div>
    <div style='height:6px'></div>
    <div id='hist' class='scroll'></div>
  </div>
</div>
<script>
function isAuthed(){try{return !!(localStorage.getItem('email')&&localStorage.getItem('password'));}catch(_){return false}}
function authHeader(){try{const e=localStorage.getItem('email'),p=localStorage.getItem('password'); if(!e||!p) return {}; return {'Authorization':'Basic '+btoa(e+':'+p)}}catch(_){return {}}}
function setHTML(id,h){document.getElementById(id).innerHTML=h}
function setText(id,t){document.getElementById(id).textContent=t}
function renderTransactions(items){if(!Array.isArray(items)||items.length===0) return '<div class="muted">No transaction history yet</div>'; return items.map(it=>`<div class="movie"><div><strong>${new Date(it.timestamp).toLocaleString()}</strong></div><div class="muted">Type: ${it.type}</div><div class="muted">Amount: ${it.amount > 0 ? '+' : ''}${it.amount}</div></div>`).join('')}
async function loadHistory(){setText('status',''); const r=await fetch('/api/users/transaction/history',{headers:authHeader()}); if(!r.ok) return setText('status','Failed to load transaction history'); const data=await r.json(); setHTML('hist', renderTransactions(data))}
(function init(){if(!isAuthed()){window.location.href='/web'; return;} document.getElementById('protected').classList.remove('hidden'); loadHistory();})();
</script>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)