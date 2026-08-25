// Guided tour — each step runs the real urlgenie package via Pyodide.
import { boot } from '../assets/urlgenie-runtime.js';

const SRC = 'https://github.com/bluestero/urlgenie/blob/main/urlgenie/';

const STEPS = [
  { id: 'welcome', kind: 'info', kicker: 'BEFORE WE START', title: 'Six small questions about a link',
    use: 'For scrapers, extractor plugins, form validation, and ETL pipelines that need one canonical record.', useLink: 'https://github.com/bluestero/urlgenie/blob/main/USE_CASES.md',
    body: 'URL Genie does not have one big “clean this” function. It has a handful of narrow checks that each answer a single question honestly, plus one canonicalizer that makes links comparable. This tour walks through them in the order you would actually use them.',
    aside: 'Every step runs the real Python package in your browser. Each one starts on an input that fails — fix it and Next unlocks.' },

  { id: 'url', kind: 'single', kicker: 'STEP 1 · VALIDATE', title: 'Is this even a real URL?', sig: 'validate_url(url, require_suffix=True)', doc: SRC + 'validate.py',
    body: 'The first filter on any scraped list. It parses the string and checks the ending against the public suffix list, so a typo like “acme.zzz” fails even though it is shaped perfectly.',
    use: 'a scraped column is half junk and every request you spend on a fake domain is a request wasted',
    aside: 'The flag is narrower than it looks. A made-up TLD is rejected by the parser itself, so turning it off changes nothing there — the only hosts it rescues are bare IP addresses, the one suffix-less form the parser keeps.',
    toggle: 'require real TLD', toggleDefault: true, val: 'https://acme.zzz',
    chips: ['https://acme.zzz', 'http://192.168.1.10/admin', 'https://example.photography/portfolio'] },

  { id: 'email', kind: 'single', kicker: 'STEP 2 · VALIDATE', title: 'Is this address theirs, or just on their page?', sig: 'validate_email(email, url=None)', doc: SRC + 'validate.py',
    body: 'On its own it is a syntax check. Pass the site URL as well and it also asks whether the address sits on that site’s registrable domain — the usual way to drop a stray Gmail address from a company scrape. Edit the url= field to try it against any site: subdomains count as a match, and a bare host works as well as a full URL.',
    use: 'the address on the page might be the company — or whoever built their website',
    toggle: 'match domain', toggleDefault: true, extra: 'https://www.example.com', val: 'agency@otherfirm.com',
    chips: ['agency@otherfirm.com', 'hello@example.com', 'info@mail.example.com', 'sample@image.png'] },

  { id: 'phone', kind: 'single', kicker: 'STEP 3 · VALIDATE', title: 'Numeric is not the same as callable', sig: 'validate_phone(phone)', doc: SRC + 'validate.py',
    body: 'It refuses anything containing letters before it counts a single digit, then enforces the E.164 range and rejects repeated digits and unbroken id-shaped runs. That ordering matters: “asdasd1312312321” has a plausible digit count and would fool anything that only counts digits.',
    use: 'a contact block hands you 1312312321 and nothing says whether that is a phone or an order id',
    val: 'asdasd1312312321', chips: ['asdasd1312312321', '+1 (555) 010-2233', '1712345678901', '4432'] },

  { id: 'social', kind: 'single', kicker: 'STEP 4 · VALIDATE', title: 'A valid URL is not a profile', sig: 'validate_social(url)', doc: SRC + 'social.py',
    body: 'The check people most often skip and most often regret. It recognises the network, then runs the platform’s own rules to see whether the path is somebody’s handle — share dialogs, group pages and search results all fail here.',
    use: 'you grabbed every social-looking link on a page and only want the ones that are somebody’s account',
    val: 'twitter.com/intent', chips: ['twitter.com/intent', 'twitter.com/natgeo', 'facebook.com/sharer/sharer.php'] },

  { id: 'profile', kind: 'single', kicker: 'STEP 5 · VALIDATE', title: 'When you need both facts separately', sig: 'validate_social_profile(url, platform)', doc: SRC + 'validate.py',
    body: 'Sometimes “is it on Facebook” and “is it a Facebook profile” need different answers. validate_social_platform answers the first, validate_social_profile the second. The same input shows the split: recognised as Facebook, but with no handle in the path.',
    use: 'enriching a share dialog as if it were a person is the kind of row that reaches your client',
    select: true, val: 'facebook.com/profile.php',
    chips: ['facebook.com/profile.php', 'facebook.com/profile.php?id=123123123', 'facebook.com/natgeo'] },

  { id: 'generalize', kind: 'single', kicker: 'STEP 6 · GENERALIZE', title: 'Two spellings, one page', sig: 'generalize(url)', doc: SRC + 'generalize.py',
    body: 'Generalization is what makes everything comparable: RFC 3986 normalization, https forced, query and fragment and trailing slash dropped. Social links go further and collapse to the canonical profile URL.',
    use: 'the same page arrives spelled four ways and you need one key to store it under',
    val: 'http://WWW.Example.com/Blog/?utm_source=newsletter',
    chips: ['http://WWW.Example.com/Blog/?utm_source=newsletter', 'fb.com/@ahmedkhatib', 'example.com/blog/'] },

  { id: 'many', kind: 'text', kicker: 'STEP 7 · GENERALIZE MANY', title: 'The same trick, at list scale', sig: 'generalize_many(urls)', doc: SRC + 'generalize.py',
    body: 'One (original, generalized) pair per input, in order — invalid entries come back as None rather than being dropped, so nothing shifts out of alignment. Group by the canonical form and duplicates collapse.',
    use: 'thousands of rows need deduping and the row order has to survive it',
    val: 'http://WWW.Example.com/Blog/?utm_source=newsletter\nhttps://example.com/blog\nexample.com/blog/\nhttps://acme.io/pricing\nhttps://www.acme.io/pricing#plans\nnot-a-link' },

  { id: 'extract', kind: 'text', kicker: 'STEP 8 · EXTRACT DATA', title: 'Everything at once, on real page text', sig: 'extract_contacts(text)', doc: SRC + 'extract.py',
    body: 'The module that uses all the others. Emails are validated, phones normalized, and social candidates run through the same platform rules as generalize — so extraction and generalization can never disagree about what counts as a profile.',
    use: 'a contact page has everything you need and you would rather not maintain four regexes to get it',
    val: 'Studio Nord — Contact\nPress: press@studionord.com · Bookings: hello@studionord.com\nCall us on +1 (555) 010-2233 (order ref 1712345678901)\nFollow: twitter.com/studionord, facebook.com/sharer/sharer.php?u=studionord.com\nPortfolio: http://WWW.studionord.com/work/?utm_source=footer' },

  { id: 'done', kind: 'final', kicker: 'DONE', title: 'You have run every module',
    body: 'Validate narrows, generalize normalizes, extract does both across raw text. That is the whole mental model — the rest is arguments.' }
];

const S = { i: 0, rt: null, vals: {}, extras: {}, toggles: {}, sels: {}, results: {}, menu: false, flip: false, platforms: ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube'] };
STEPS.forEach(s => {
  if (s.val != null) S.vals[s.id] = s.val;
  if (s.toggle) S.toggles[s.id] = !!s.toggleDefault;
  if (s.extra) S.extras[s.id] = s.extra;
  if (s.select) S.sels[s.id] = 'facebook';
});

const $ = s => document.querySelector(s);
const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
const cur = () => STEPS[S.i];
const passed = () => { const s = cur(); const r = S.results[s.id]; return s.kind === 'info' || s.kind === 'final' || !!(r && r.ok); };

function copy(text) { try { navigator.clipboard.writeText(text); } catch (e) {} }
function flash(btn, label) { const was = btn.textContent; btn.textContent = label; setTimeout(() => { btn.textContent = was; }, 1400); }
function markSeen() { try { localStorage.setItem('urlgenie_tour_seen', '1'); } catch (e) {} }

$('#theme').addEventListener('click', () => {
  const t = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem('urlgenie_theme', t); } catch (e) {}
});
$('#skip').addEventListener('click', markSeen);

function renderRail() {
  const rail = $('#rail');
  rail.textContent = '';
  STEPS.forEach((s, n) => {
    const b = el('button', n === S.i ? 'now' : (n < S.i ? 'done' : ''));
    b.title = s.title;
    b.addEventListener('click', () => go(n));
    rail.appendChild(b);
  });
  $('#counter').textContent = (S.i + 1) + ' / ' + STEPS.length;
}

function go(n) {
  S.i = Math.max(0, Math.min(STEPS.length - 1, n));
  S.menu = false; S.flip = !S.flip;
  renderRail(); render();
}

function next() {
  if (!passed()) { run(); return; }
  if (S.i < STEPS.length - 1) go(S.i + 1);
}

function run() {
  const s = cur();
  if (!S.rt || s.kind === 'info' || s.kind === 'final') return;
  const v = S.vals[s.id] != null ? S.vals[s.id] : (s.val || '');
  const on = !!S.toggles[s.id];
  const p = S.sels[s.id] || 'facebook';
  let r;
  try {
    if (s.id === 'url') r = S.rt.call('url', { v, suffix: on });
    else if (s.id === 'email') r = S.rt.call('email', { v, site: on ? (S.extras.email || '') : '' });
    else if (s.id === 'profile') r = S.rt.call('profile', { v, p });
    else if (s.id === 'many') {
      const g = S.rt.call('many', { v });
      r = { ok: true, list: g.groups.map(x => ({ tag: x.ok ? '×' + x.count : 'invalid', ok: x.ok, main: x.canon || 'no canonical form', note: x.inputs.join('  ·  ') })) };
    } else if (s.id === 'extract') {
      const e = S.rt.call('extract', { v });
      const rows = [];
      Object.keys(e).forEach(k => e[k].forEach(val => rows.push({ tag: k, ok: true, main: val, note: '' })));
      r = { ok: rows.length > 0, list: rows };
    } else r = S.rt.call(s.id, { v });
  } catch (err) { r = { ok: false, message: String(err.message || err), detail: '' }; }
  S.results[s.id] = r;
  render();
}

function render() {
  const s = cur(), host = $('#step');
  host.textContent = '';
  host.className = 'step' + (S.flip ? ' alt' : '');

  const copyBox = el('div', 'copy');
  copyBox.appendChild(el('span', 'kick', s.kicker));
  copyBox.appendChild(el('h1', null, s.title));
  copyBox.appendChild(el('div', 'body', s.body));
  if (s.use) {
    const w = el('div', 'when');
    w.appendChild(el('span', 'lab', s.kind === 'info' ? 'BUILT FOR' : 'REACH FOR IT WHEN'));
    const txt = el('span', 'txt', s.use);
    if (s.useLink) {
      const a = el('a', null, ' See all use cases →');
      a.href = s.useLink; a.target = '_blank'; a.rel = 'noopener';
      txt.appendChild(a);
    }
    w.appendChild(txt);
    copyBox.appendChild(w);
  }
  if (s.aside) copyBox.appendChild(el('div', 'aside', s.aside));
  host.appendChild(copyBox);

  if (s.kind === 'single' || s.kind === 'text') host.appendChild(exercise(s));
  if (s.kind === 'final') host.appendChild(finalCard());
  host.appendChild(navBar());
}

function exercise(s) {
  const box = el('div', 'exercise');

  const head = el('div', 'exhead');
  head.appendChild(el('code', 'sig', s.sig));
  const tools = el('div', 'tools');
  const cp = el('button', 'ghost', 'copy call');
  cp.addEventListener('click', () => {
    const first = String(S.vals[s.id] != null ? S.vals[s.id] : (s.val || '')).split('\n')[0];
    copy('urlgenie.' + s.sig.replace(/\(.*/, '') + '("' + first + '")');
    flash(cp, 'copied');
  });
  const src = el('a', 'ghost btn', 'source ↗');
  src.href = s.doc; src.target = '_blank'; src.rel = 'noopener';
  tools.appendChild(cp); tools.appendChild(src);
  head.appendChild(tools);
  box.appendChild(head);

  if (s.kind === 'single') {
    const row = el('div', 'row');
    const input = el('input');
    input.value = S.vals[s.id] || ''; input.spellcheck = false;
    input.addEventListener('input', e => { S.vals[s.id] = e.target.value; });
    input.addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
    row.appendChild(input);

    if (s.extra && S.toggles[s.id]) {
      const wrap = el('div', 'extra');
      wrap.appendChild(el('span', null, 'url='));
      const ex = el('input');
      ex.value = S.extras[s.id] || ''; ex.placeholder = 'https://www.example.com'; ex.spellcheck = false;
      ex.addEventListener('input', e => { S.extras[s.id] = e.target.value; });
      ex.addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
      wrap.appendChild(ex);
      row.appendChild(wrap);
    }

    if (s.toggle) {
      const sw = el('button', 'sw plain');
      sw.setAttribute('role', 'switch');
      sw.setAttribute('aria-checked', String(!!S.toggles[s.id]));
      const track = el('span', 'track'); track.appendChild(el('span', 'knob'));
      sw.appendChild(track);
      sw.appendChild(el('span', 'label', s.toggle));
      sw.addEventListener('click', () => { S.toggles[s.id] = !S.toggles[s.id]; render(); });
      row.appendChild(sw);
    }

    if (s.select) {
      const sel = el('div', 'sel');
      const btn = el('button', 'plain');
      btn.appendChild(document.createTextNode(S.sels[s.id] || 'facebook'));
      btn.appendChild(el('i', null, '▼'));
      btn.addEventListener('click', e => { e.stopPropagation(); S.menu = !S.menu; render(); });
      sel.appendChild(btn);
      if (S.menu) {
        const menu = el('div', 'menu');
        S.platforms.forEach(p => {
          const o = el('button', 'plain', p);
          o.setAttribute('aria-current', String(S.sels[s.id] === p));
          o.addEventListener('click', () => { S.sels[s.id] = p; S.menu = false; render(); });
          menu.appendChild(o);
        });
        sel.appendChild(menu);
      }
      row.appendChild(sel);
    }

    const go2 = el('button', 'solid', S.rt ? 'Check' : 'starting…');
    go2.disabled = !S.rt;
    go2.addEventListener('click', run);
    row.appendChild(go2);
    box.appendChild(row);
  } else {
    const col = el('div', 'textcol');
    const ta = el('textarea');
    ta.rows = 6; ta.spellcheck = false; ta.value = S.vals[s.id] || '';
    ta.addEventListener('input', e => { S.vals[s.id] = e.target.value; });
    col.appendChild(ta);
    const go2 = el('button', 'solid', S.rt ? 'Run it' : 'starting…');
    go2.disabled = !S.rt;
    go2.addEventListener('click', run);
    col.appendChild(go2);
    box.appendChild(col);
  }

  if (s.chips && s.chips.length) {
    const sug = el('div', 'suggested');
    sug.appendChild(el('span', null, 'SUGGESTED'));
    s.chips.forEach(c => {
      const b = el('button', 'chip', c);
      b.addEventListener('click', () => { S.vals[s.id] = c; render(); });
      sug.appendChild(b);
    });
    box.appendChild(sug);
  }

  const r = S.results[s.id];
  if (r && !r.list) {
    const res = el('div', 'result');
    res.appendChild(el('span', 'badge' + (r.ok ? ' ok' : ''), r.ok ? 'Valid' : 'Invalid'));
    const text = el('div', 'text');
    text.appendChild(el('div', 'msg', r.message || ''));
    if (r.detail) text.appendChild(el('div', 'detail', r.detail));
    res.appendChild(text);
    box.appendChild(res);
  }
  if (r && r.list) {
    const rows = el('div', 'rows');
    r.list.forEach(x => {
      const row = el('div', 'r');
      row.appendChild(el('span', 'tag' + (x.ok ? '' : ' bad'), x.tag));
      const cell = el('div', 'cell');
      cell.appendChild(el('span', 'main', x.main));
      if (x.note) cell.appendChild(el('span', 'note', x.note));
      row.appendChild(cell);
      rows.appendChild(row);
    });
    box.appendChild(rows);
  }
  return box;
}

function finalCard() {
  const box = el('div', 'final');
  box.appendChild(el('strong', null, 'That is the whole library.'));
  box.appendChild(el('p', null, 'The playground has every module on one page, with the examples you just ran already loaded. Everything runs in your browser — nothing you type leaves the page.'));
  const a = el('a', null, 'Open the playground →');
  a.href = '../playground/';
  a.addEventListener('click', markSeen);
  box.appendChild(a);
  return box;
}

function navBar() {
  const nav = el('div', 'nav');
  const back = el('button', 'back', '← Back');
  back.disabled = S.i === 0;
  back.addEventListener('click', () => go(S.i - 1));
  nav.appendChild(back);

  const right = el('div', 'right');
  const ok = passed(), last = S.i === STEPS.length - 1;
  if (!ok) right.appendChild(el('span', 'hint', S.rt ? 'Get a valid result to continue' : 'Starting the Python runtime…'));
  const nx = el('button', 'next' + (ok && !last ? '' : ' locked'), last ? 'Finished' : 'Next →');
  nx.disabled = !ok || last;
  nx.addEventListener('click', next);
  right.appendChild(nx);
  nav.appendChild(right);
  return nav;
}

window.addEventListener('keydown', e => {
  if (e.target && /INPUT|TEXTAREA/.test(e.target.tagName)) return;
  if (e.key === 'ArrowRight') next();
  if (e.key === 'ArrowLeft') go(S.i - 1);
});
document.addEventListener('click', () => { if (S.menu) { S.menu = false; render(); } });

renderRail();
render();

boot(t => { $('#bootText').textContent = 'Starting the real Python package in your browser — ' + t; })
  .then(rt => {
    S.rt = rt;
    S.platforms = rt.call('platforms', {});
    $('#boot').hidden = true;
    render();
  })
  .catch(e => { $('#bootText').textContent = 'failed to start — ' + e.message; });
