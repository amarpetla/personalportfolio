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
  renderExperience(data);
  renderEducation(data);
  renderSkills(data);
  renderCerts(data);
  renderContact(data);
}

function renderSummary(data){
  const about = data.SUMMARY || data.PROFILE || data.ABOUT || (Array.isArray(data.UNCLASSIFIED)? data.UNCLASSIFIED.slice(0,1): null);
  if (about){
    document.getElementById('about-content').innerHTML = about.map(p=>`<p>${esc(p)}</p>`).join('\n');
  }
}

function renderExperience(data){
  const target = document.getElementById('experience-list');
  if (data.EXPERIENCE_STRUCTURED){
    target.innerHTML = data.EXPERIENCE_STRUCTURED.map(exp=>expItem(exp)).join('\n');
  } else {
    const fallback = data['EXPERIENCE'] || data['WORK EXPERIENCE'] || [];
    target.innerHTML = fallback.map(t=>`<div class="item"><p>${esc(t)}</p></div>`).join('\n');
  }
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
  const target = document.getElementById('education-list');
  if (data.EDUCATION_STRUCTURED){
    target.innerHTML = data.EDUCATION_STRUCTURED.map(e=>`<div class="item"><h3>${esc(e.degree||'')}</h3>${e.institution? `<div class="meta">${esc(e.institution)}</div>`:''}${e.details? `<p>${esc(e.details)}</p>`:''}</div>`).join('\n');
  } else if (data.EDUCATION){
    target.innerHTML = data.EDUCATION.map(e=>`<div class="item"><p>${esc(e)}</p></div>`).join('\n');
  }
}

function renderSkills(data){
  const list = document.getElementById('skills-list');
  if (data.SKILLS_GROUPED){
    list.innerHTML = Object.entries(data.SKILLS_GROUPED).map(([group, skills])=>{
      const chips = skills.slice(0,12).map(s=>`<li>${esc(s)}</li>`).join('');
      return `<li class="skill-group"><strong>${esc(group)}</strong><ul class="chips subgroup">${chips}</ul></li>`;
    }).join('\n');
  } else if (data.SKILLS_FLAT){
    list.innerHTML = data.SKILLS_FLAT.map(s=>`<li>${esc(s)}</li>`).join('\n');
  } else {
    const skills = data.SKILLS || data['TECHNICAL SKILLS'] || [];
    list.innerHTML = skills.map(s=>`<li>${esc(s)}</li>`).join('\n');
  }
}

function renderCerts(data){
  const projectsWrap = document.getElementById('projects-list');
  if (data.CERTIFICATIONS_STRUCTURED){
    projectsWrap.innerHTML = `<div class="item"><h3>Certifications</h3><ul class="bullets">${data.CERTIFICATIONS_STRUCTURED.map(c=>`<li>${esc(c)}</li>`).join('')}</ul></div>`;
  } else {
    projectsWrap.innerHTML = '<p>No certifications parsed.</p>';
  }
}

function renderContact(data){
  if (!data.CONTACT) return;
  const c = data.CONTACT;
  if (c.email){
    const emailEl = document.getElementById('contact-email');
    emailEl.textContent = c.email; emailEl.href = `mailto:${c.email}`;
  } else { document.getElementById('contact-email').parentElement.style.display='none'; }
  if (c.linkedin){
    const li = document.getElementById('contact-linkedin');
    li.textContent = 'LinkedIn'; li.href = c.linkedin;
  }
  if (c.github){
    const gh = document.getElementById('contact-github'); gh.textContent='GitHub'; gh.href=c.github;
  } else {
    document.getElementById('contact-github').style.display='none';
  }
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
