const form = document.getElementById('uploadForm');
const result = document.getElementById('result');
const codeEl = document.getElementById('code');
const linkEl = document.getElementById('link');


form.addEventListener('submit', async (e) => {
e.preventDefault();
const f = document.getElementById('fileInput').files[0];
const expiry = document.getElementById('expiry').value;
if (!f) return alert('Choose a file');
const fd = new FormData();
fd.append('file', f);
fd.append('expire_hours', expiry);


const res = await fetch('/upload', { method: 'POST', body: fd });
if (!res.ok) {
const txt = await res.text();
alert('Upload failed: ' + txt);
return;
}
const data = await res.json();
codeEl.textContent = data.code;
linkEl.textContent = data.download_url;
linkEl.href = data.download_url;
result.style.display = 'block';
});