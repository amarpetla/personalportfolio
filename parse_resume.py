import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

from pdfminer.high_level import extract_text

PDF_PATH = Path('resume/staff_Amar_Petla.pdf')
OUTPUT_JSON = Path('resume/parsed_resume.json')
OUTPUT_RAW = Path('resume/resume_text.txt')
JSON_RESUME = Path('resume/json_resume.json')
SITE_JSON = Path('site/parsed_resume.json')
SITE_JSON_RESUME = Path('site/json_resume.json')
ROOT_JSON = Path('parsed_resume.json')
ROOT_JSON_RESUME = Path('json_resume.json')

SECTION_NAME_REGEX = re.compile(r'^[A-Z][A-Z &/+-]{2,}$')
COMMON_SECTIONS = [
    'SUMMARY', 'PROFILE', 'ABOUT', 'SKILLS', 'TECHNICAL SKILLS', 'EXPERIENCE', 'PROFESSIONAL EXPERIENCE',
    'WORK EXPERIENCE', 'EDUCATION', 'PROJECTS', 'CERTIFICATIONS', 'ACHIEVEMENTS', 'AWARDS', 'PUBLICATIONS',
    'VOLUNTEER', 'VOLUNTEER EXPERIENCE', 'LEADERSHIP', 'EXPERIENCE HIGHLIGHTS', 'WORK HISTORY', 'ACCOMPLISHMENTS'
]
EMBEDDED_HEADINGS = [
    'SKILLS', 'EXPERIENCE HIGHLIGHTS', 'WORK HISTORY', 'WORK EXPERIENCE', 'EXPERIENCE', 'EDUCATION', 'ACCOMPLISHMENTS', 'CERTIFICATIONS'
]

EMAIL_REGEX = re.compile(r'(?<![A-Za-z0-9._%+-])[A-Za-z][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,10}\b')
PHONE_REGEX = re.compile(r'(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}')
LINKEDIN_REGEX = re.compile(r'linkedin\.com/(?:in|pub)/[A-Za-z0-9-_/]+', re.IGNORECASE)
GITHUB_REGEX = re.compile(r'github\.com/[A-Za-z0-9-_/]+', re.IGNORECASE)
DATE_RANGE_REGEX = re.compile(r'(20\d{2}-\d{2})\s*-\s*(Current|20\d{2}-\d{2})')
CITY_STATE_REGEX = re.compile(r'([A-Z][A-Za-z .]+),\s*([A-Z]{2})\b')
TITLE_CORE_REGEX = re.compile(
    r'^(?P<title>(?:(?:Staff|Senior|Sr\.?|Lead|Principal|Software|Big\s*Data|Data|Solutions?|Solution|Platform|Cloud|AI|ML|Machine\s*Learning)\s+)*'
    r'(?:Engineer|Architect|Developer|Manager|Analyst))\b',
    re.IGNORECASE
)

# Detect beginning of descriptive text to cut off from company/title lines
DESC_CUTOFF_REGEX = re.compile(
    r'\b(Responsibilities|Achievements|Projects|Technologies|Technology|Summary|Description|Role|Responsibilities:|Built|Implemented|Designed|Led|Responsible|Worked|Developed|Migrated|Modernized|Created|Managed|Mentored|Delivered|Drove)\b',
    re.IGNORECASE
)

# Allowed tokens often present in company names; used to keep only the company portion
COMPANY_KEEP_TOKENS = {
    '&', 'and', 'of', 'the', 'Inc', 'Inc.', 'LLC', 'Ltd', 'Ltd.', 'Co', 'Co.', 'Corp', 'Corp.', 'Corporation',
    'Company', 'Technologies', 'Technology', 'Systems', 'Financial', 'Services', 'Bank', 'Solutions', 'Labs', 'Group'
}

BULLET_PREFIX = '\u2022'

SKILL_GROUP_KEYWORDS = {
    'cloud': 'Cloud & Platforms',
    'azure': 'Cloud & Platforms',
    'gcp': 'Cloud & Platforms',
    'aws': 'Cloud & Platforms',
    'snowflake': 'Data Warehousing',
    'big query': 'Data Warehousing',
    'spark': 'Big Data & Processing',
    'hadoop': 'Big Data & Processing',
    'kafka': 'Streaming & Messaging',
    'pub/sub': 'Streaming & Messaging',
    'sql': 'Databases',
    'postgres': 'Databases',
    'postgresql': 'Databases',
    'mysql': 'Databases',
    'hbase': 'Databases',
    'scala': 'Languages',
    'python': 'Languages',
    'java': 'Languages',
    'spring': 'Frameworks',
    'rest': 'Frameworks',
    'airflow': 'Orchestration',
    'composer': 'Orchestration',
    'databricks': 'Platforms',
    'terraform': 'DevOps',
    'jenkins': 'DevOps',
    'github actions': 'DevOps',
    'snowpark': 'ML & AI',
    'vertex ai': 'ML & AI',
    'ml': 'ML & AI',
    'pytorch': 'ML & AI',
    'tensor': 'ML & AI',
    'scikit': 'ML & AI',
    'pandas': 'ML & AI',
    'numpy': 'ML & AI'
}

# ----------------- Preprocessing -----------------

def normalize_text(text: str) -> str:
    text = text.replace('\x0c', '\n')
    text = re.sub(r'([^\n])' + BULLET_PREFIX, r'\1\n' + BULLET_PREFIX, text)
    text = re.sub(r'(?<!\n)(?=[12][09]\d{2}-\d{2}\s*-\s*(?:Current|[12][09]\d{2}-\d{2}))', '\n', text)
    text = re.sub(r'(?<!\n)(Responsibilities:)', r'\n\1', text)
    return text

# ----------------- Section heuristics -----------------

def is_section_heading(line: str) -> bool:
    l = line.strip()
    if not l:
        return False
    if l.upper() != l:
        return False
    if len(l) > 48:
        return False
    if SECTION_NAME_REGEX.match(l):
        return True
    if l in COMMON_SECTIONS:
        return True
    return False

def segment_sections(lines: List[str]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = 'UNCLASSIFIED'
    sections[current] = []
    for line in lines:
        raw = line.strip('\u2022 ').rstrip()
        if is_section_heading(raw):
            current = raw
            sections.setdefault(current, [])
            continue
        if not raw:
            sections[current].append('')
        else:
            sections[current].append(raw)
    return sections

def post_process(sections: Dict[str, List[str]]) -> Dict[str, List[str]]:
    processed: Dict[str, List[str]] = {}
    for name, lines in sections.items():
        items: List[str] = []
        buf: List[str] = []
        for l in lines + ['']:
            if l == '':
                if buf:
                    items.append(' '.join(buf).strip())
                    buf = []
            else:
                buf.append(l)
        processed[name] = items
    return processed

def secondary_inline_split(sections: Dict[str, List[str]]) -> Dict[str, List[str]]:
    if 'UNCLASSIFIED' not in sections:
        return sections
    blob_items = sections['UNCLASSIFIED']
    if len(blob_items) <= 1:
        blob_text = ' '.join(blob_items) if blob_items else ''
    else:
        return sections
    if not blob_text or len(blob_text) < 200:
        return sections
    blob_text = re.sub(r'\s+', ' ', blob_text)
    positions: List[Tuple[int, str]] = []
    for heading in EMBEDDED_HEADINGS:
        for m in re.finditer(r'\b' + re.escape(heading) + r'\b', blob_text):
            positions.append((m.start(), heading))
    if not positions:
        return sections
    positions.sort()
    new_sections: Dict[str, List[str]] = {}
    first_start = positions[0][0]
    preface = blob_text[:first_start].strip()
    if preface and len(preface.split()) > 5:
        new_sections['SUMMARY'] = [preface]
    for idx, (start, heading) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(blob_text)
        segment = blob_text[start:end].strip()
        seg_body = segment[len(heading):].strip(' -:')
        parts = re.split(r'(?<=[.;])\s+(?=[A-Z(])', seg_body)
        cleaned = [p.strip() for p in parts if p.strip()]
        if heading.startswith('SKILL'):
            skills_joined = ' '.join(cleaned)
            skill_tokens = re.split(r'[;,]\s*', skills_joined)
            cleaned = [s.strip() for s in skill_tokens if s.strip()]
        new_sections[heading] = cleaned
    merged: Dict[str, List[str]] = {k: v for k, v in sections.items() if k != 'UNCLASSIFIED'}
    if any(v for v in new_sections.values()):
        merged.update(new_sections)
        return merged
    return sections

# ----------------- Contacts -----------------

def _normalize_phone(match_text: str) -> str:
    digits = re.sub(r'\D', '', match_text)
    # Handle leading country code 1
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    # Fallback: return only digits
    return digits

def extract_contacts(text: str) -> Dict[str, str]:
    contacts: Dict[str, str] = {}
    # Normalize whitespace and strip common glue characters around tokens
    cleaned_text = re.sub(r'[\u200b\u200c\u200d]', '', text)

    # Email: prefer token-based exact match to avoid glued noise
    email_candidates: List[str] = []
    for tok in re.split(r'\s+', cleaned_text):
        if '@' not in tok:
            continue
        # Remove leading phone fragments and trailing URL bits
        tok = re.sub(r'^[0-9+\-().]+', '', tok)
        tok = tok.strip('.,;:()[]{}<>\'\"')
        tok = re.sub(r'(https?:.*)$', '', tok, flags=re.IGNORECASE)
        m = EMAIL_REGEX.search(tok)
        if m:
            email_candidates.append(m.group(0))
    if not email_candidates:
        # Fallback: scan whole text
        email_candidates = EMAIL_REGEX.findall(cleaned_text)
    if email_candidates:
        seen = set()
        dedup = []
        for e in email_candidates:
            if e not in seen:
                seen.add(e)
                dedup.append(e)
        # Prefer common providers to avoid accidental matches
        preferred = next((e for e in dedup if any(p in e.lower() for p in ['gmail.', 'outlook.', 'yahoo.', 'proton.'])), dedup[0])
        contacts['email'] = preferred

    # Phone: first valid pattern, normalized to 999-999-9999
    pm = PHONE_REGEX.search(cleaned_text)
    if pm:
        contacts['phone'] = _normalize_phone(pm.group(0))

    # LinkedIn: canonicalize and lowercase
    li = LINKEDIN_REGEX.search(cleaned_text)
    if li:
        link = li.group(0)
        link = re.sub(r'^https?://', '', link, flags=re.IGNORECASE)
        contacts['linkedin'] = 'https://' + link.lower().rstrip('/ ')

    # GitHub (optional)
    gh = GITHUB_REGEX.search(cleaned_text)
    if gh:
        link = gh.group(0)
        link = re.sub(r'^https?://', '', link, flags=re.IGNORECASE)
        contacts['github'] = 'https://' + link.rstrip('/ ')

    return contacts

# ----------------- Experience -----------------

def _preclean_title_line(s: str) -> str:
    s = re.sub(r'\s+', ' ', s).strip()
    # Insert space where PDF glued words (lowercase followed by Uppercase)
    s = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s)
    # Also insert space where an ALLCAPS token is glued to a TitleCase word (e.g., "AZBuilt" -> "AZ Built")
    s = re.sub(r'([A-Z]{2,})(?=[A-Z][a-z])', r'\1 ', s)
    return s

def _trim_company_tokens(company: str) -> str:
    # Cut at obvious description starters
    company = re.split(DESC_CUTOFF_REGEX, company)[0].strip()
    if not company:
        return company
    toks = company.split()
    kept = []
    for t in toks:
        # Allow tokens that look like Company Name parts or common suffixes
        t_stripped = t.strip('()[]{}')
        if re.match(r"^[A-Z][A-Za-z0-9&.'-]*$", t_stripped) or t_stripped in COMPANY_KEEP_TOKENS:
            kept.append(t)
        else:
            # Stop at first token that clearly looks like sentence continuation (lowercase or punctuation-heavy)
            break
    # If we kept nothing (all lowercase?), fallback to original up to first comma/pipe/dash
    if not kept:
        kept = re.split(r"[,|\-]", company, 1)[0].split()
    # Limit overly long companies
    if len(kept) > 6:
        kept = kept[:6]
    return ' '.join(kept).strip("-, |")

def derive_company_location(title_line: str) -> Tuple[str, str, str]:
    tl = _preclean_title_line(title_line)
    # Cut off any trailing descriptive text early
    tl = re.split(DESC_CUTOFF_REGEX, tl)[0].strip()
    # Find the last City, ST occurrence as the location
    loc_match = None
    for m in CITY_STATE_REGEX.finditer(tl):
        loc_match = m
    location = ''
    head = tl
    if loc_match:
        location = loc_match.group(0)
        head = tl[:loc_match.start()].rstrip(' ,-|')
    else:
        # Fallback: trailing ALLCAPS city token(s) (e.g., PHOENIX)
        tail_city = re.search(r'(?:,?\s*)([A-Z]{3,}(?:\s[A-Z]{3,})*)$', tl)
        if tail_city:
            loc = tail_city.group(1).strip()
            if len(loc) >= 4 and loc.replace(' ', '').isupper():
                location = loc
                head = tl[:tail_city.start()].rstrip(' ,-|')

    # Try to extract a title from the start and treat the remainder as company
    title = ''
    company = ''
    m = TITLE_CORE_REGEX.search(head)
    if m:
        title = _preclean_title_line(m.group('title'))
        company = head[m.end():].strip(' ,-|')
    else:
        # Fallback: split by two or more spaces or by last comma
        if ',' in head:
            pre, post = head.rsplit(',', 1)
            title = pre.strip()
            company = post.strip()
        else:
            parts = head.split()
            if len(parts) > 2:
                title = ' '.join(parts[:-2])
                company = ' '.join(parts[-2:])
            else:
                title = head

    # Final cleanup
    title = title.strip(' -|,')
    company = _trim_company_tokens(company.strip(' -|,')) if company else ''
    return title, company, location

def parse_experience(lines: List[str]) -> List[Dict[str, Any]]:
    experiences: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        dr = DATE_RANGE_REGEX.search(line)
        if not dr:
            i += 1
            continue
        start_date, end_date = dr.group(1), dr.group(2)
        post = line[dr.end():].strip()
        title_line = post
        bullets: List[str] = []
        j = i + 1
        while j < n:
            nxt = lines[j].strip()
            if DATE_RANGE_REGEX.search(nxt):
                break
            if nxt.startswith(BULLET_PREFIX):
                bullets.append(nxt.lstrip(BULLET_PREFIX).strip())
            elif nxt.startswith('Responsibilities:'):
                bullets.append(nxt)
            elif nxt:
                if not title_line:
                    title_line = nxt
                else:
                    if not bullets:
                        title_line += ' ' + nxt
                    else:
                        bullets[-1] += ' ' + nxt
            j += 1
        title, company, location = derive_company_location(title_line)
        experiences.append({
            'start': start_date,
            'end': end_date,
            'title': title,
            'company': company,
            'location': location,
            'bullets': bullets
        })
        i = j
    return experiences

# ----------------- Education / Certifications / Skills -----------------

def parse_education(text: str) -> List[Dict[str, str]]:
    edu_block_match = re.search(r'(Education|EDUCATION)(.*?)(Accomplishments|ACHIEVEMENTS|CERTIFICATIONS|$)', text, re.DOTALL)
    if not edu_block_match:
        return []
    block = edu_block_match.group(2)
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    entries: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for l in lines:
        if re.search(r'Master|Bachelor|B\.Sc|M\.Sc', l, re.IGNORECASE):
            if current:
                entries.append(current)
                current = {}
            current['degree'] = l
        elif any(loc_word in l for loc_word in ['University', 'Institute', 'College']):
            current['institution'] = l
        else:
            current['details'] = (current.get('details', '') + ' ' + l).strip()
    if current:
        entries.append(current)
    return entries

def parse_certifications(text: str) -> List[str]:
    m = re.search(r'(Certifications|CERTIFICATIONS)(.*?)(Education|EDUCATION|Skills|SKILLS|$)', text, re.DOTALL)
    if not m:
        # fallback previous tail search
        m2 = re.search(r'(Certifications|CERTIFICATIONS)(.*)', text, re.DOTALL)
        if not m2:
            return []
        block = m2.group(2)
    else:
        block = m.group(2)
    block = block.replace('\r', ' ')
    # Break on newlines, commas, or camel-case boundaries with 'Certification' / 'Certified'
    parts = re.split(r'\n|,', block)
    out: List[str] = []
    for p in parts:
        p = p.strip(' -:\u2022')
        if not p:
            continue
        # Further split long glued segments containing 'Certification' or 'Certified'
        sub_segs = re.split(r'(?<=Certification)(?=[A-Z])|(?<=Certified)(?=[A-Z])', p)
        for seg in sub_segs:
            s = seg.strip()
            if not s or len(s) < 3:
                continue
            if any(k in s.lower() for k in ['cert', 'azure', 'snowflake', 'ai', 'cloud']):
                if s not in out:
                    out.append(s)
    return out

def parse_skill_block(text: str) -> List[str]:
    m = re.search(r'Skills(.*?)(Work History|WORK HISTORY|Experience|EXPERIENCE)', text, re.DOTALL)
    if not m:
        return []
    block = m.group(1).replace('\n', ' ')
    parts = re.split(r'[;,]', block)
    cleaned = []
    for p in parts:
        s = p.strip(' -:\u2022')
        if 1 < len(s) < 60 and not s.lower().startswith('skills'):
            if s not in cleaned:
                cleaned.append(s)
    return cleaned

def group_skills(skills: List[str]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for skill in skills:
        key = None
        low = skill.lower()
        for kw, group in SKILL_GROUP_KEYWORDS.items():
            if kw in low:
                key = group
                break
        if not key:
            key = 'Other'
        grouped.setdefault(key, []).append(skill)
    # Deduplicate per group preserving order
    for k, vals in grouped.items():
        seen = set()
        deduped = []
        for v in vals:
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        grouped[k] = deduped
    return grouped

# ----------------- JSON Resume Export -----------------

def extract_name(text: str) -> str:
    # First line tokens until lowercase appears
    first_line = text.strip().splitlines()[0]
    tokens = first_line.strip().split()
    name_tokens = []
    for t in tokens:
        if t and (t[0].isupper() and not t.isupper()):
            name_tokens.append(t)
        elif len(name_tokens) >= 2:
            break
    if not name_tokens and tokens:
        return tokens[0]
    return ' '.join(name_tokens)[:60]

def build_json_resume(structured: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    name = extract_name(raw_text)
    contact = structured.get('CONTACT', {})
    work = []
    for exp in structured.get('EXPERIENCE_STRUCTURED', []):
        work.append({
            'name': exp.get('company') or '',
            'position': exp.get('title') or '',
            'location': exp.get('location') or '',
            'startDate': exp.get('start'),
            'endDate': None if exp.get('end','').lower() == 'current' else exp.get('end'),
            'summary': (exp.get('bullets') or [''])[0][:300] if exp.get('bullets') else '',
            'highlights': exp.get('bullets') or []
        })
    education = []
    for edu in structured.get('EDUCATION_STRUCTURED', []):
        education.append({
            'institution': edu.get('institution',''),
            'studyType': edu.get('degree',''),
            'area': '',
            'startDate': '',
            'endDate': '',
            'score': '',
            'courses': []
        })
    skills_flat = structured.get('SKILLS_FLAT', [])
    grouped = group_skills(skills_flat)
    skills_section = [{'name': group, 'keywords': kws} for group, kws in grouped.items()]
    certificates = [{'name': c} for c in structured.get('CERTIFICATIONS_STRUCTURED', [])]
    jr = {
        'basics': {
            'name': name,
            'email': contact.get('email',''),
            'phone': contact.get('phone',''),
            'url': contact.get('linkedin','')
        },
        'work': work,
        'education': education,
        'skills': skills_section,
        'certificates': certificates,
        'meta': { 'generator': 'parse_resume.py' }
    }
    return jr

# ----------------- Main -----------------

def main():
    if not PDF_PATH.exists():
        raise SystemExit(f'Missing PDF at {PDF_PATH}')
    raw_text = extract_text(str(PDF_PATH))
    normalized = normalize_text(raw_text)
    OUTPUT_RAW.write_text(normalized, encoding='utf-8')
    lines = [l.rstrip() for l in normalized.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    sections = segment_sections(lines)
    structured = post_process(sections)
    structured = secondary_inline_split(structured)

    contacts = extract_contacts(normalized)
    if contacts:
        structured['CONTACT'] = contacts

    experiences = parse_experience(lines)
    if experiences:
        structured['EXPERIENCE_STRUCTURED'] = experiences

    education_entries = parse_education(normalized)
    if education_entries:
        structured['EDUCATION_STRUCTURED'] = education_entries

    certs = parse_certifications(normalized)
    if certs:
        structured['CERTIFICATIONS_STRUCTURED'] = certs

    flat_skills = parse_skill_block(normalized)
    if flat_skills:
        structured['SKILLS_FLAT'] = flat_skills
        structured['SKILLS_GROUPED'] = group_skills(flat_skills)

    OUTPUT_JSON.write_text(json.dumps(structured, indent=2), encoding='utf-8')

    # JSON Resume export
    json_resume = build_json_resume(structured, normalized)
    JSON_RESUME.write_text(json.dumps(json_resume, indent=2), encoding='utf-8')

    # Copy into site for static hosting and root for GitHub Pages
    try:
        if SITE_JSON.parent.exists():
            SITE_JSON.write_text(OUTPUT_JSON.read_text(encoding='utf-8'), encoding='utf-8')
        if SITE_JSON_RESUME.parent.exists():
            SITE_JSON_RESUME.write_text(JSON_RESUME.read_text(encoding='utf-8'), encoding='utf-8')
        ROOT_JSON.write_text(OUTPUT_JSON.read_text(encoding='utf-8'), encoding='utf-8')
        ROOT_JSON_RESUME.write_text(JSON_RESUME.read_text(encoding='utf-8'), encoding='utf-8')
    except Exception as e:
        print(f'Copy to site failed: {e}')

    print(f'Wrote raw text to {OUTPUT_RAW}')
    print(f'Wrote structured JSON to {OUTPUT_JSON}')
    print(f'Wrote JSON Resume to {JSON_RESUME}')

if __name__ == '__main__':
    main()
