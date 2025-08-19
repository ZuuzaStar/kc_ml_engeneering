from fastapi import APIRouter
from fastapi.responses import HTMLResponse

web_ui = APIRouter()

@web_ui.get("/web", response_class=HTMLResponse)
async def web_index():
    html = """
<!DOCTYPE html>
<html>
<head><title>Movie Recommender</title></head>
<body>
<h1>Movie Recommender</h1>

<section>
  <h2>Signup</h2>
  <label>Email: <input id="s_email" type="email"></label><br/>
  <label>Password: <input id="s_password" type="password"></label><br/>
  <button onclick="signup()">Sign up</button>
  <pre id="signup_result"></pre>
</section>

<section>
  <h2>Login + Get Balance</h2>
  <label>Email: <input id="email" type="email"></label><br/>
  <label>Password: <input id="password" type="password"></label><br/>
  <button onclick="getBalance()">Get Balance (auth)</button>
  <pre id="balance"></pre>
</section>

<section>
  <h2>New Prediction</h2>
  <label>Prompt: <input id="prompt" type="text" size="60"></label><br/>
  <label>Top: <input id="top" type="number" value="10"></label><br/>
  <button onclick="newPrediction()">Request</button>
  <pre id="pred"></pre>
</section>

<section>
  <h2>Prediction History</h2>
  <button onclick="getHistory()">Load History</button>
  <pre id="hist"></pre>
</section>

<script>
function basicHeader() {
  const e = document.getElementById('email').value;
  const p = document.getElementById('password').value;
  const token = btoa(e + ":" + p);
  return {"Authorization": "Basic " + token};
}
async function signup() {
  const payload = {
    email: document.getElementById('s_email').value,
    password: document.getElementById('s_password').value
  };
  const r = await fetch('/api/users/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  document.getElementById('signup_result').textContent = await r.text();
}
async function getBalance() {
  const r = await fetch('/api/users/balance-auth', { headers: basicHeader() });
  document.getElementById('balance').textContent = await r.text();
}
async function newPrediction() {
  const msg = encodeURIComponent(document.getElementById('prompt').value);
  const top = encodeURIComponent(document.getElementById('top').value);
  const r = await fetch('/api/events/prediction/new-auth?message=' + msg + '&top=' + top, {
    method: 'POST',
    headers: basicHeader()
  });
  document.getElementById('pred').textContent = await r.text();
}
async function getHistory() {
  const r = await fetch('/api/events/prediction/history-auth', { headers: basicHeader() });
  document.getElementById('hist').textContent = await r.text();
}
</script>
</body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)