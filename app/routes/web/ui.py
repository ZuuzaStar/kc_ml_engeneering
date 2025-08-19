from fastapi import APIRouter
from fastapi.responses import HTMLResponse

web_ui = APIRouter()

BASE_CSS = """
  :root { --bg:#0b1220; --card:#121a2b; --muted:#7c92b2; --text:#e6edf7; --accent:#4f7cff; --accent-2:#2bd4a5; --danger:#ff5d5d; --border:#1f2a44; }
  *{box-sizing:border-box}
  body{margin:0;padding:24px;font-family:ui-sans-serif,system-ui,-apple-system,Roboto;background:radial-gradient(1200px 800px at 20% -10%,#17233a 0%,transparent 50%),radial-gradient(1000px 600px at 110% 10%,#0f1a30 0%,transparent 40%),var(--bg);color:var(--text)}
  a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}
  .container{max-width:1100px;margin:0 auto}
  .grid{display:grid;grid-template-columns:1fr;gap:16px} @media(min-width:900px){.grid{grid-template-columns:360px 1fr}}
  .card{background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.01));border:1px solid var(--border);border-radius:14px;padding:16px;backdrop-filter:blur(6px);box-shadow:0 6px 20px rgba(0,0,0,.25)}
  .title{font-size:22px;margin:0 0 8px;letter-spacing:.3px}
  .muted{color:var(--muted);font-size:14px}
  .row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
  .input{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:10px;background:#0e1526;color:var(--text)}
  .btn{padding:10px 14px;border-radius:10px;border:1px solid var(--border);background:#0f172a;color:var(--text);cursor:pointer}
  .btn.primary{background:linear-gradient(90deg,var(--accent),#7a9aff);border:none;color:#fff}
  .btn.success{background:linear-gradient(90deg,var(--accent-2),#35e3b3);border:none;color:#07271e}
  .stack{display:flex;flex-direction:column;gap:10px}
  .scroll{max-height:420px;overflow:auto;border:1px solid var(--border);border-radius:12px;padding:10px;background:#0c1426}
  .movie{display:grid;grid-template-columns:1fr;gap:6px;padding:12px;border-bottom:1px dashed var(--border)} .movie:last-child{border-bottom:0}
  .tag{display:inline-block;padding:2px 8px;font-size:12px;border-radius:999px;background:#0d1b36;border:1px solid var(--border);color:var(--muted);margin-right:6px}
  .topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
  .link{color:var(--muted)} .error{color:var(--danger);font-size:13px;min-height:18px}
"""

@web_ui.get("/web", response_class=HTMLResponse)
async def web_index():
    html = """
<!DOCTYPE html><html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Movie Recommender</title>""" + "<style>" + BASE_CSS + "</style>" + """</head>
<body><div class='container'>
  <div class='topbar'>
    <div class='row' style='gap:12px;'><strong>Movie Recommender</strong><span class='muted'>Demo</span></div>
    <a class='link' href='/web/history'>History →</a>
  </div>
  <div class='grid'>
    <div class='stack'>
      <div class='card'>
        <h3 class='title'>Auth</h3>
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
      <div class='card'>
        <h3 class='title'>Balance</h3>
        <div class='stack'>
          <div class='row'><button class='btn' onclick='getBalance()'>Refresh</button><strong id='balance' style='font-size:18px;'>—</strong></div>
          <div class='row'><input id='topup' class='input' type='number' min='1' step='1' placeholder='Top up amount' style='max-width:180px;'/><button class='btn success' onclick='topUp()'>Top up</button></div>
          <div id='balance_error' class='error'></div>
        </div>
      </div>
    </div>
    <div class='card'>
      <h3 class='title'>Recommendations</h3>
      <div class='stack'>
        <input id='prompt' class='input' type='text' placeholder='What would you like to watch?'/>
        <div class='row'><input id='top' class='input' type='number' min='1' value='10' style='max-width:120px;'/><button class='btn primary' onclick='newPrediction()'>Request</button></div>
        <div id='pred_list' class='scroll' aria-live='polite'></div>
        <div id='pred_error' class='error'></div>
      </div>
    </div>
  </div>
</div>
<script>
function setCreds(e,p){localStorage.setItem('email',e);localStorage.setItem('password',p)}
function getCreds(){return {email:localStorage.getItem('email')||document.getElementById('email').value,password:localStorage.getItem('password')||document.getElementById('password').value}}
function authHeader(){const c=getCreds(); if(!c.email||!c.password) return {}; return {'Authorization':'Basic '+btoa(c.email+':'+c.password)}}
function setText(id,t){document.getElementById(id).textContent=t}
function setHTML(id,h){document.getElementById(id).innerHTML=h}
async function signup(){const e=document.getElementById('email').value,p=document.getElementById('password').value; if(!e||!p) return setText('auth_msg','Enter email & password'); const r=await fetch('/api/users/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})}); setCreds(e,p); setText('auth_msg',r.ok?'Signed up':'Signup failed'); if(r.ok) getBalance()}
async function signin(){const e=document.getElementById('email').value,p=document.getElementById('password').value; if(!e||!p) return setText('auth_msg','Enter email & password'); const r=await fetch('/api/users/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})}); setCreds(e,p); setText('auth_msg',r.ok?'Signed in':'Signin failed'); if(r.ok) getBalance()}
async function getBalance(){setText('balance_error',''); const r=await fetch('/api/users/balance-auth',{headers:authHeader()}); if(!r.ok) return setText('balance_error','Unable to fetch balance'); try{const d=await r.json(); setText('balance', (d['Current balance']??'—'));}catch(e){setText('balance','—')}}
async function topUp(){setText('balance_error',''); const a=parseFloat(document.getElementById('topup').value||'0'); const {email}=getCreds(); if(!email||!a) return setText('balance_error','Enter amount & be logged in'); const r=await fetch('/api/users/balance/adjust',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email,amount:a})}); if(!r.ok) return setText('balance_error','Top up failed'); getBalance()}
function renderMovies(list){if(!Array.isArray(list)||list.length===0) return '<div class="muted">No recommendations yet</div>'; return list.map(m=>`<div class="movie"><div><strong>${m.title??'-'} (${m.year??'-'})</strong></div><div class="muted">${(m.description??'').slice(0,320)}</div><div>${(m.genres||[]).map(g=>`<span class="tag">${g}</span>`).join('')}</div></div>`).join('')}
async function newPrediction(){setText('pred_error',''); const msg=document.getElementById('prompt').value.trim(); const top=parseInt(document.getElementById('top').value||'10',10); if(!msg) return setText('pred_error','Enter your request'); const r=await fetch(`/api/events/prediction/new-auth?message=${encodeURIComponent(msg)}&top=${top}`,{method:'POST',headers:authHeader()}); if(!r.ok){const err=await r.text(); return setText('pred_error', err||'Request failed')} const data=await r.json(); setHTML('pred_list', renderMovies(data))}
(function init(){const e=localStorage.getItem('email'),p=localStorage.getItem('password'); if(e) document.getElementById('email').value=e; if(p) document.getElementById('password').value=p; if(e&&p) getBalance()})();
</script>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)


@web_ui.get("/web/history", response_class=HTMLResponse)
async def web_history():
    html = """
<!DOCTYPE html><html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Prediction History</title>""" + "<style>" + BASE_CSS + "</style>" + """</head>
<body><div class='container'>
  <div class='topbar'><a class='link' href='/web'>← Back</a><strong>History</strong><span></span></div>
  <div class='card'>
    <div class='row' style='justify-content:space-between;'>
      <div class='row' style='gap:8px;'><input id='email' class='input' type='email' placeholder='Email' style='max-width:260px;'/><input id='password' class='input' type='password' placeholder='Password' style='max-width:180px;'/><button class='btn' onclick='loadHistory()'>Load</button></div>
      <span id='status' class='muted'></span>
    </div>
    <div style='height:6px'></div>
    <div id='hist' class='scroll'></div>
  </div>
</div>
<script>
function authHeader(){const e=localStorage.getItem('email')||document.getElementById('email').value; const p=localStorage.getItem('password')||document.getElementById('password').value; if(!e||!p) return {}; return {'Authorization':'Basic '+btoa(e+':'+p)}}
function setHTML(id,h){document.getElementById(id).innerHTML=h}
function setText(id,t){document.getElementById(id).textContent=t}
function renderHistory(items){if(!Array.isArray(items)||items.length===0) return '<div class="muted">No history yet</div>'; return items.map(it=>`<div class="movie"><div><strong>${new Date(it.timestamp).toLocaleString()}</strong></div><div class="muted">Prompt: ${it.input_text}</div><div class="muted">Cost: ${it.cost}</div><div>${(it.movies||[]).map(m=>`<span class="tag">${m.title}</span>`).join('')}</div></div>`).join('')}
async function loadHistory(){setText('status',''); const r=await fetch('/api/events/prediction/history-auth',{headers:authHeader()}); if(!r.ok) return setText('status','Failed to load'); const data=await r.json(); setHTML('hist', renderHistory(data))}
(function init(){const e=localStorage.getItem('email'),p=localStorage.getItem('password'); if(e) document.getElementById('email').value=e; if(p) document.getElementById('password').value=p; if(e&&p) loadHistory()})();
</script>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)