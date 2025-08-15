// Portfolio rendering & interactivity enhancements
async function loadResume() {
  document.getElementById('year').textContent = new Date().getFullYear();
  try {
    // Use local site copy for static deployments (GitHub Pages)
    const res = await fetch('parsed_resume.json');
    if (!res.ok) throw new Error('Resume JSON not found yet');
    const data = await res.json();
    window.__RESUME_DATA__ = data;
    render(data);
    setupDownloads();
  } catch (e) {
    console.warn('Resume load issue:', e.message);
  }
}

function esc(str){return (str||'').replace(/[&<>\"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

function render(data){
  renderSummary(data);
  // Static HTML is now used for Experience, Projects, Skills, Education, and Contact sections.
}

function renderSummary(data){
  // Use SUMMARY or ABOUT or PROFILE or UNCLASSIFIED
  let aboutArr = data.SUMMARY || data.PROFILE || data.ABOUT || (Array.isArray(data.UNCLASSIFIED)? data.UNCLASSIFIED: []);
  if (!Array.isArray(aboutArr)) aboutArr = [aboutArr];
  // Split into summary (first) and profile (rest)
  const summary = aboutArr.length ? aboutArr[0] : '';
  const profile = aboutArr.length > 1 ? aboutArr.slice(1).join(' ') : '';
  document.getElementById('about-summary').innerHTML = summary ? `<p>${esc(summary)}</p>` : '';
  document.getElementById('about-profile').innerHTML = profile ? `<p>${esc(profile)}</p>` : '';
}

function renderExperience(data){
  // Experience section is now static HTML.
}

function expItem(exp){
  const allBullets = (exp.bullets||[]).filter(b=>b && b.trim());
  const shown = allBullets.slice(0,6).map(b=>`<li>${esc(b)}</li>`).join('');
  const hidden = allBullets.slice(6).map(b=>`<li>${esc(b)}</li>`).join('');
  const metaParts = [exp.company, exp.location].filter(Boolean).join(' | ');
  const collapse = hidden ? `<button class="more-btn" data-state="closed">Show more (${allBullets.length-6})</button><ul class="bullets hidden">${hidden}</ul>` : '';
  return `<div class="item"><h3>${esc(exp.title)}</h3><div class="meta">${esc(exp.start)} – ${esc(exp.end)}${metaParts? ' | '+esc(metaParts):''}</div>${allBullets.length? `<ul class="bullets">${shown}</ul>${collapse}`:''}</div>`;
}

function renderEducation(data){
  // Education section is now static HTML.
}

function renderSkills(data){
  // Skills section is now static HTML.
}

function renderCerts(data){
  // Projects section is now static HTML.
}

function renderContact(data){
  // Contact section is now static HTML.
}

function setupDownloads(){
  const dlWrap = document.getElementById('download-links');
  if (!dlWrap) return;
  dlWrap.innerHTML = `
    <a href="parsed_resume.json" download>Raw JSON</a>
    <a href="json_resume.json" download>JSON Resume</a>
  `;
}

function delegateClicks(){
  document.body.addEventListener('click', e => {
    const btn = e.target.closest('.more-btn');
    if (btn){
      const state = btn.getAttribute('data-state');
      const hiddenList = btn.nextElementSibling;
      if (state === 'closed'){
        hiddenList.classList.remove('hidden');
        btn.textContent = 'Show less';
        btn.setAttribute('data-state','open');
      } else {
        hiddenList.classList.add('hidden');
        btn.textContent = `Show more (${hiddenList.children.length})`;
        btn.setAttribute('data-state','closed');
        hiddenList.scrollIntoView({behavior:'smooth', block:'nearest'});
      }
    }
    const themeToggle = e.target.closest('#theme-toggle');
    if (themeToggle){
      document.documentElement.classList.toggle('light');
      localStorage.setItem('theme', document.documentElement.classList.contains('light')? 'light':'dark');
    }
  });
  const saved = localStorage.getItem('theme');
  if (saved === 'light') document.documentElement.classList.add('light');
}

document.addEventListener('DOMContentLoaded', () => { loadResume(); delegateClicks(); });
// End
