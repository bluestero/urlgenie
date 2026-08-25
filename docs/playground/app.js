// Playground — every answer comes from the real urlgenie package via Pyodide.
import { boot } from '../assets/urlgenie-runtime.js';

const SRC = 'https://github.com/bluestero/urlgenie/blob/main/urlgenie/';

const DEFS = {
  url: {
    name: 'Is this a real URL?', sig: 'validate_url(url)', doc: SRC + 'validate.py',
    desc: 'Parses the string, then checks the ending against the public suffix list. Note the flag is narrow: a made-up TLD is rejected by the parser itself, so require_suffix only ever changes the answer for bare IP addresses.',
    when: 'a scraped column is half junk and every request you spend on a fake domain is a request wasted',
    ph: 'https://example.com/page', toggle: 'require real TLD', toggleDefault: true,
    val: 'https://example.photography/portfolio',
    chips: ['https://example.photography/portfolio', 'https://acme.zzz', 'http://192.168.1.10/admin', 'definitely not a url']
  },
  email: {
    name: 'Is this email real — and theirs?', sig: 'validate_email(email, url=None)', doc: SRC + 'validate.py',
    desc: 'Syntax first, with RFC 5321 length limits and a filename-extension blocklist. Turn on “match domain” and the url= field appears: point it at any site and the address must sit on that site’s registrable domain. A bare host works as well as a full URL, and subdomains count as a match.',
    when: 'the address on the page might be the company — or whoever built their website',
    ph: 'hello@example.com', toggle: 'match domain', extraPh: 'https://www.example.com', extra: 'https://www.example.com',
    val: 'sample@image.png',
    chips: ['sample@image.png', 'hello@example.com', 'info@mail.example.com', 'agency@otherfirm.com']
  },
  phone: {
    name: 'Is this number callable?', sig: 'validate_phone(phone)', doc: SRC + 'validate.py',
    desc: 'Rejects anything containing letters before it counts a digit, then enforces the E.164 range and drops repeated digits and unbroken id-shaped runs.',
    when: 'a contact block hands you 1312312321 and nothing says whether that is a phone or an order id',
    ph: '+1 (555) 010-2233', val: 'asdasd1312312321',
    chips: ['+1 (555) 010-2233', 'asdasd1312312321', '1712345678901', '4432']
  },
  social: {
    name: 'Is this a social profile?', sig: 'validate_social(url)', doc: SRC + 'social.py',
    desc: 'Recognises the network, then runs that platform’s own rules over the path. Reserved routes, share dialogs and search pages are not profiles no matter how valid the URL is.',
    when: 'you grabbed every social-looking link on a page and only want the ones that are somebody’s account',
    ph: 'twitter.com/handle', val: 'twitter.com/intent',
    chips: ['twitter.com/intent', 'twitter.com/natgeo', 'fb.com/@ahmedkhatib', 'example.com/about']
  },
  splat: {
    name: 'Is it on this platform at all?', sig: 'validate_social_platform(url, platform)', doc: SRC + 'validate.py',
    desc: 'The narrow question: does this URL’s domain belong to the platform you named? It says nothing about what the page is. Aliases like fb and x resolve to their canonical platform.',
    when: 'a mixed pile of links needs splitting per network before anyone looks closer',
    ph: 'facebook.com/anything', select: true, val: 'facebook.com/profile.php',
    chips: ['facebook.com/profile.php', 'facebook.com/natgeo', 'twitter.com/natgeo']
  },
  sprof: {
    name: 'Is it a profile on this platform?', sig: 'validate_social_profile(url, platform)', doc: SRC + 'validate.py',
    desc: 'The same input as above shows the split: recognised as Facebook, but with no handle in the path. Add an id and it passes.',
    when: 'enriching a share dialog as if it were a person is the kind of row that reaches your client',
    ph: 'facebook.com/handle', select: true, val: 'facebook.com/profile.php',
    chips: ['facebook.com/profile.php', 'facebook.com/profile.php?id=123123123', 'facebook.com/natgeo']
  },
  gen: {
    name: 'Canonical form of one URL', sig: 'generalize(url)', doc: SRC + 'generalize.py',
    desc: 'RFC 3986 normalization — scheme and host case, percent-encoding, dot segments, default ports — then query, fragment and trailing slash are dropped. Recognised social links collapse further, to the canonical profile URL.',
    when: 'the same page arrives spelled four ways and you need one key to store it under',
    ph: 'http://WWW.Example.com/Blog/?utm_source=x', val: 'http://WWW.Example.com/Blog/?utm_source=x',
    chips: ['http://WWW.Example.com/Blog/?utm_source=x', 'fb.com/@ahmedkhatib', 'example.com/blog/']
  },
  many: {
    bulk: true, name: 'Generalize many', sig: 'generalize_many(urls)', doc: SRC + 'generalize.py',
    desc: 'Runs the same canonicalization across a list and groups the results, so you can see at a glance which of your links were secretly the same page.',
    when: 'thousands of rows need deduping and the row order has to survive it',
    run: 'Generalize all', sample: 'load a messy sample',
    fill: 'http://WWW.Example.com/Blog/?utm_source=newsletter\nhttps://example.com/blog\nexample.com/blog/\nhttps://acme.io/pricing\nhttps://www.acme.io/pricing#plans\nnot-a-link'
  },
  extract: {
    bulk: true, name: 'Extract data', sig: 'extract_contacts(text)', doc: SRC + 'extract.py',
    desc: 'Emails are validated, phones normalized, and social candidates run through the same platform rules as generalize — so extraction and generalization can never disagree about what counts as a profile.',
    when: 'a contact page has everything you need and you would rather not maintain four regexes to get it',
    run: 'Extract', sample: 'load a sample contact page',
    fill: 'Studio Nord — Contact\nPress: press@studionord.com · Bookings: hello@studionord.com\nCall us on +1 (555) 010-2233 (order ref 1712345678901)\nFollow: twitter.com/studionord, facebook.com/sharer/sharer.php?u=studionord.com\nPortfolio: http://WWW.studionord.com/work/?utm_source=footer'
  }
};

const NAV = [
  { label: 'VALIDATE',
    head: ['Six independent yes/no checks', 'Each answers a single question and returns a plain true or false. They are deliberately separate: a URL can be valid and not social, social and not a profile, numeric and not a phone.'],
    items: [['url', 'validate_url'], ['email', 'validate_email'], ['phone', 'validate_phone'], ['social', 'validate_social'], ['splat', 'validate_social_platform'], ['sprof', 'validate_social_profile']] },
  { label: 'GENERALIZE',
    head: ['One URL in, one canonical URL out', 'Generalization is what makes everything else comparable. Run it before you store, dedupe or diff a link.'],
    items: [['gen', 'generalize'], ['many', 'generalize_many']] },
  { label: 'EXTRACT',
    head: ['Raw text in, sorted contacts out', 'The end-to-end module: it finds contact-shaped things in a blob of page text and validates each one on the way out.'],
    items: [['extract', 'extract_contacts']] }
];

const S = {
  rt: null, fn: 'url', platforms: ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube'],
  vals: {}, extras: {}, toggles: {}, sels: {}, results: {}, bulk: {}, bulkOut: {}, menu: false
};
Object.keys(DEFS).forEach(k => {
  const d = DEFS[k];
  if (d.bulk) S.bulk[k] = '';
  else { S.vals[k] = d.val || ''; S.toggles[k] = !!d.toggleDefault; if (d.extra) S.extras[k] = d.extra; if (d.select) S.sels[k] = 'facebook'; }
});
try {
  const saved = localStorage.getItem('urlgenie_fn');
  if (saved && DEFS[saved]) S.fn = saved;
} catch (e) {}
if (location.hash.slice(1) && DEFS[location.hash.slice(1)]) S.fn = location.hash.slice(1);

const $ = s => document.querySelector(s);
const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };

/* ---------- header ---------- */
$('#theme').addEventListener('click', () => {
  const t = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem('urlgenie_theme', t); } catch (e) {}
});

let toastTimer;
$('#install').addEventListener('click', () => {
  copy('pip install urlgenie');
  $('#toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 2500);
});

try {
  if (!localStorage.getItem('urlgenie_tour_seen')) $('#invite').hidden = false;
} catch (e) {}
$('#dismiss').addEventListener('click', () => {
  try { localStorage.setItem('urlgenie_tour_seen', '1'); } catch (e) {}
  $('#invite').hidden = true;
});

function copy(text) { try { navigator.clipboard.writeText(text); } catch (e) {} }

function flash(btn, label) {
  const was = btn.textContent;
  btn.textContent = label;
  setTimeout(() => { btn.textContent = was; }, 1400);
}

function status(text, ready) {
  $('#statustext').textContent = text;
  $('#status').classList.toggle('ready', !!ready);
}

/* ---------- sidebar ---------- */
function renderSide() {
  const side = $('#side');
  side.textContent = '';
  NAV.forEach(g => {
    const box = el('div', 'group');
    box.appendChild(el('span', 'grouplabel', g.label));
    g.items.forEach(([key, label]) => {
      const b = el('button', 'plain', label);
      b.setAttribute('aria-current', String(S.fn === key));
      b.addEventListener('click', () => {
        S.fn = key; S.menu = false;
        try { localStorage.setItem('urlgenie_fn', key); } catch (e) {}
        history.replaceState(null, '', '#' + key);
        renderSide(); renderPane();
      });
      box.appendChild(b);
    });
    side.appendChild(box);
  });
}

/* ---------- pane ---------- */
function groupOf(fn) { return NAV.find(g => g.items.some(i => i[0] === fn)) || NAV[0]; }

function renderPane() {
  const pane = $('#pane');
  const d = DEFS[S.fn];
  pane.textContent = '';

  const intro = el('div', 'intro');
  const g = groupOf(S.fn);
  const h2 = el('h2', null, g.head[0]);
  intro.appendChild(h2);
  intro.appendChild(el('p', null, g.head[1]));
  pane.appendChild(intro);

  pane.appendChild(d.bulk ? bulkCard(d) : singleCard(d));
}

function cardHead(d) {
  const head = el('div', 'cardhead');
  const left = el('div', 'left');
  const titles = el('div', 'titles');
  titles.appendChild(el('h3', null, d.name));
  titles.appendChild(el('code', 'sig', d.sig));
  left.appendChild(titles);
  left.appendChild(el('div', 'desc', d.desc));

  const when = el('div', 'when');
  when.appendChild(el('span', 'kicker', 'REACH FOR IT WHEN'));
  when.appendChild(el('span', null, d.when));
  left.appendChild(when);

  const tools = el('div', 'tools');
  const cp = el('button', 'ghost', 'copy call');
  cp.addEventListener('click', () => {
    const arg = d.bulk ? 'text' : '"' + (S.vals[S.fn] || '') + '"';
    copy('urlgenie.' + d.sig.replace(/\(.*/, '') + '(' + arg + ')');
    flash(cp, 'copied');
  });
  const src = el('a', 'ghost btn', 'source ↗');
  src.href = d.doc; src.target = '_blank'; src.rel = 'noopener';
  tools.appendChild(cp); tools.appendChild(src);

  head.appendChild(left); head.appendChild(tools);
  return head;
}

function singleCard(d) {
  const card = el('div', 'card');
  card.appendChild(cardHead(d));

  const row = el('div', 'row');
  const input = el('input');
  input.value = S.vals[S.fn] || ''; input.placeholder = d.ph || ''; input.spellcheck = false;
  input.addEventListener('input', e => { S.vals[S.fn] = e.target.value; });
  input.addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
  row.appendChild(input);

  if (d.extraPh && S.toggles[S.fn]) {
    const wrap = el('div', 'extra');
    wrap.appendChild(el('span', null, 'url='));
    const ex = el('input');
    ex.value = S.extras[S.fn] || ''; ex.placeholder = d.extraPh; ex.spellcheck = false;
    ex.addEventListener('input', e => { S.extras[S.fn] = e.target.value; });
    ex.addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
    wrap.appendChild(ex);
    row.appendChild(wrap);
  }

  if (d.toggle) {
    const sw = el('button', 'sw plain');
    sw.setAttribute('role', 'switch');
    sw.setAttribute('aria-checked', String(!!S.toggles[S.fn]));
    const track = el('span', 'track'); track.appendChild(el('span', 'knob'));
    sw.appendChild(track);
    sw.appendChild(el('span', 'label', d.toggle));
    sw.addEventListener('click', () => { S.toggles[S.fn] = !S.toggles[S.fn]; renderPane(); });
    row.appendChild(sw);
  }

  if (d.select) {
    const sel = el('div', 'sel');
    const btn = el('button', 'plain');
    btn.appendChild(document.createTextNode(S.sels[S.fn] || 'facebook'));
    btn.appendChild(el('i', null, '▼'));
    btn.addEventListener('click', e => { e.stopPropagation(); S.menu = !S.menu; renderPane(); });
    sel.appendChild(btn);
    if (S.menu) {
      const menu = el('div', 'menu');
      S.platforms.forEach(p => {
        const o = el('button', 'plain', p);
        o.setAttribute('aria-current', String(S.sels[S.fn] === p));
        o.addEventListener('click', () => { S.sels[S.fn] = p; S.menu = false; renderPane(); });
        menu.appendChild(o);
      });
      sel.appendChild(menu);
    }
    row.appendChild(sel);
  }

  const go = el('button', 'solid', S.rt ? 'Check' : 'starting…');
  go.disabled = !S.rt;
  go.addEventListener('click', run);
  row.appendChild(go);
  card.appendChild(row);

  const tryRow = el('div', 'try');
  tryRow.appendChild(el('span', null, 'TRY'));
  (d.chips || []).forEach(c => {
    const b = el('button', 'chip', c);
    b.addEventListener('click', () => { S.vals[S.fn] = c; renderPane(); });
    tryRow.appendChild(b);
  });
  card.appendChild(tryRow);

  const r = S.results[S.fn];
  if (r) {
    const res = el('div', 'result');
    res.appendChild(el('span', 'badge' + (r.ok ? ' ok' : ''), r.ok ? 'Valid' : 'Invalid'));
    const text = el('div', 'text');
    text.appendChild(el('div', 'msg', r.message || ''));
    if (r.detail) text.appendChild(el('div', 'detail', r.detail));
    res.appendChild(text);
    card.appendChild(res);
  }
  return card;
}

function bulkCard(d) {
  const card = el('div', 'card');
  card.appendChild(cardHead(d));

  const ta = el('textarea');
  ta.rows = 7; ta.spellcheck = false; ta.value = S.bulk[S.fn] || '';
  ta.addEventListener('input', e => { S.bulk[S.fn] = e.target.value; });
  card.appendChild(ta);

  const row = el('div', 'row');
  const go = el('button', 'solid', S.rt ? d.run : 'starting…');
  go.disabled = !S.rt;
  go.addEventListener('click', run);
  const sample = el('button', 'softbtn', d.sample);
  sample.addEventListener('click', () => { S.bulk[S.fn] = d.fill; renderPane(); });
  row.appendChild(go); row.appendChild(sample);
  row.appendChild(el('span', 'spacer'));

  const out = S.bulkOut[S.fn];
  const rows = bulkRows();
  if (out) {
    const ex = el('div', 'exports');
    ex.appendChild(el('span', 'count', S.fn === 'many'
      ? out.total + ' in · ' + out.groups.length + ' unique'
      : rows.length + ' found'));
    const cj = el('button', 'softbtn', 'copy JSON');
    cj.addEventListener('click', () => { copy(JSON.stringify(out, null, 2)); flash(cj, 'copied'); });
    const cs = el('button', 'softbtn', 'download CSV');
    cs.addEventListener('click', downloadCsv);
    ex.appendChild(cj); ex.appendChild(cs);
    row.appendChild(ex);
  }
  card.appendChild(row);

  if (out) {
    const box = el('div', 'rows');
    rows.forEach(x => {
      const r = el('div', 'r');
      r.appendChild(el('span', 'tag' + (x.ok ? '' : ' bad'), x.tag));
      const cell = el('div', 'cell');
      cell.appendChild(el('span', 'main', x.main));
      if (x.note) cell.appendChild(el('span', 'note', x.note));
      r.appendChild(cell);
      box.appendChild(r);
    });
    card.appendChild(box);
  }
  return card;
}

function bulkRows() {
  const out = S.bulkOut[S.fn];
  if (!out) return [];
  if (S.fn === 'many') {
    return out.groups.map(g => ({
      tag: g.ok ? '×' + g.count : 'invalid', ok: g.ok,
      main: g.canon || 'no canonical form', note: g.inputs.join('  ·  ')
    }));
  }
  const rows = [];
  Object.keys(out).forEach(k => out[k].forEach(v => rows.push({ tag: k, ok: true, main: v, note: '' })));
  return rows;
}

function downloadCsv() {
  const out = S.bulkOut[S.fn], esc = s => '"' + String(s).replace(/"/g, '""') + '"';
  const csv = S.fn === 'many'
    ? 'original,generalized\n' + out.groups.flatMap(g => g.inputs.map(i => esc(i) + ',' + esc(g.canon || ''))).join('\n')
    : 'kind,value\n' + bulkRows().map(r => esc(r.tag) + ',' + esc(r.main)).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = 'urlgenie-' + S.fn + '.csv';
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ---------- run ---------- */
function run() {
  if (!S.rt) return;
  const fn = S.fn, d = DEFS[fn];
  try {
    if (d.bulk) {
      S.bulkOut[fn] = S.rt.call(fn, { v: S.bulk[fn] || '' });
    } else {
      const v = S.vals[fn] || '';
      let r;
      if (fn === 'url') r = S.rt.call('url', { v, suffix: !!S.toggles.url });
      else if (fn === 'email') r = S.rt.call('email', { v, site: S.toggles.email ? (S.extras.email || '') : '' });
      else if (fn === 'splat') r = S.rt.call('platform', { v, p: S.sels.splat });
      else if (fn === 'sprof') r = S.rt.call('profile', { v, p: S.sels.sprof });
      else if (fn === 'gen') r = S.rt.call('generalize', { v });
      else r = S.rt.call(fn, { v });
      S.results[fn] = r;
    }
  } catch (e) {
    if (!d.bulk) S.results[fn] = { ok: false, message: String(e.message || e), detail: '' };
  }
  renderPane();
}

document.addEventListener('click', () => { if (S.menu) { S.menu = false; renderPane(); } });

renderSide();
renderPane();

boot(status)
  .then(rt => {
    S.rt = rt;
    S.platforms = rt.call('platforms', {});
    status('urlgenie v' + rt.version + ' via Pyodide', true);
    renderPane();
  })
  .catch(e => status('failed to start — ' + e.message));
