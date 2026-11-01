const app = document.getElementById('app');

const LOGO_SVG = `<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M32 32L32 3.5A28.5 28.5 0 0 1 52.15 11.85Z" style="fill:var(--nypd)" fill-opacity="0.25"/>
  <circle cx="32" cy="32" r="28.5" stroke-width="3" style="stroke:var(--airforce)"/>
  <circle cx="32" cy="32" r="15" stroke-width="3" style="stroke:var(--airforce)"/>
  <path d="M32 32L52.15 11.85" stroke-width="3.5" stroke-linecap="round" style="stroke:var(--nypd)"/>
  <circle cx="32" cy="32" r="3.5" style="fill:var(--brand)"/>
  <path d="M40.5 35V32.5A2.5 2.5 0 0 1 43 30H47A2.5 2.5 0 0 1 49.5 32.5V35" stroke-width="6.5" stroke-linecap="round" style="stroke:var(--bg)"/>
  <path d="M40.5 35V32.5A2.5 2.5 0 0 1 43 30H47A2.5 2.5 0 0 1 49.5 32.5V35" stroke-width="2.6" style="stroke:var(--brand)"/>
  <rect x="34.5" y="34.5" width="21" height="15.5" rx="3.5" stroke-width="2.6" style="fill:var(--brand);stroke:var(--bg)"/>
  <path d="M36 41.5H54" stroke-width="1.6" style="stroke:var(--bg)"/>
</svg>`;

const RINGS_SVG = `<svg class="rings" viewBox="0 0 420 420" fill="none" aria-hidden="true">
  <circle cx="210" cy="210" r="209" style="stroke:var(--line)"/>
  <circle cx="210" cy="210" r="148" style="stroke:var(--line)"/>
  <circle cx="210" cy="210" r="88" style="stroke:var(--line)"/>
  <path d="M210 210L58 58" stroke-width="1.5" style="stroke:var(--nypd)" stroke-opacity="0.6"/>
  <circle cx="130" cy="150" r="5" style="fill:var(--nypd)"/>
  <circle cx="262" cy="118" r="4" style="fill:var(--airforce)"/>
  <circle cx="300" cy="260" r="4" style="fill:var(--gap)"/>
</svg>`;

document.querySelector('.logo-mark').innerHTML = LOGO_SVG;

/* ---------- helpers ---------- */

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value == null || value === false) continue;
    if (key === 'class') el.className = value;
    else if (key.startsWith('on')) el.addEventListener(key.slice(2), value);
    else el.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat(Infinity)) {
    if (child == null || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}

function svg(markup) {
  const wrap = document.createElement('div');
  wrap.innerHTML = markup.trim();
  return wrap.firstElementChild;
}

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

const fmt = n => Number(n).toLocaleString('pl-PL');
const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);
const date = iso => iso ? new Date(iso).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' }) : null;
const daysLeft = iso => iso ? Math.ceil((new Date(iso) - Date.now()) / 86400000) : null;

function setPage(...nodes) {
  app.replaceChildren(...nodes);
  window.scrollTo(0, 0);
}

function loading() {
  setPage(h('div', { class: 'stack' }, h('div', { class: 'skeleton', style: 'width:40%;height:40px' }),
    h('div', { class: 'skeleton', style: 'width:25%' }), h('div', { class: 'skeleton', style: 'height:220px;border-radius:20px' })));
}

function failed(err) {
  setPage(h('div', { class: 'empty' }, svg(RINGS_SVG), h('h2', {}, 'Nie udało się pobrać danych'),
    h('p', { class: 'error' }, String(err.message || err)),
    h('p', {}, 'Sprawdź, czy działa baza w Dockerze i serwer API.')));
}

function tag(name, tone) {
  return h('span', { class: `tag ${tone || ''}` }, name);
}

function techTags(list, max) {
  const items = max ? list.slice(0, max) : list;
  const rest = max && list.length > max ? list.length - max : 0;
  return h('div', { class: 'tags' }, items.map(t => tag(t.name, t.have ? 'have' : '')), rest ? tag(`+${rest}`) : null);
}

function ring(have, total) {
  const ratio = total ? have / total : 0;
  const c = 2 * Math.PI * 19;
  const color = total === 0 ? 'var(--bar)' : ratio >= 0.5 ? 'var(--signal)' : 'var(--gap)';
  return h('div', { class: 'ring', title: `Masz ${have} z ${total} technologii z tej oferty` },
    svg(`<svg viewBox="0 0 46 46"><circle cx="23" cy="23" r="19" fill="none" stroke-width="4" style="stroke:var(--subtle)"/>
      <circle cx="23" cy="23" r="19" fill="none" stroke-width="4" stroke-linecap="round" style="stroke:${color}"
      stroke-dasharray="${(ratio * c).toFixed(1)} ${c.toFixed(1)}"/></svg>`),
    h('span', {}, total ? `${have}/${total}` : '–'));
}

function meter(label, value, ratio, cls = '') {
  return h('div', { class: `meter ${cls}` },
    h('div', { class: 'meter-top' }, h('span', {}, label), h('span', { class: 'mono' }, value)),
    h('div', { class: 'meter-track' }, h('div', { class: 'meter-fill', style: `width:${Math.max(2, Math.round(ratio * 100))}%` })));
}

/* ---------- Strona główna: recap i analiza rynku ---------- */

async function renderMarket() {
  loading();
  const [summary, techAll, levels, techJunior, profile, matches] = await Promise.all([
    api('/api/summary'), api('/api/stats/technologies?limit=12'), api('/api/stats/levels'),
    api('/api/stats/technologies?level=junior&limit=10'), api('/api/profile'),
    api('/api/match?level=junior&limit=3').catch(() => null),
  ]);

  const haveTop = techAll.filter(t => t.have).slice(0, 2);
  const topTwoAreMine = techAll.slice(0, 2).every(t => t.have);
  const juniorPct = pct(summary.junior, summary.total);
  const sentence = haveTop.length === 2
    ? `Tylko ${juniorPct}% ofert jest dla juniorów — ale ${haveTop[0].name} i ${haveTop[1].name}, które masz w CV, ` +
      (topTwoAreMine ? 'to dwie najczęściej wymagane technologie na całym rynku.' : 'są w czołówce najczęściej wymaganych technologii.')
    : `Tylko ${juniorPct}% ofert jest dla juniorów.`;

  const chart = h('div', { class: 'bars' });
  const gaps = h('div');
  const drawChart = list => {
    const max = Math.max(...list.map(t => t.count), 1);
    chart.replaceChildren(...list.map(t => h('div', { class: `bar-row ${t.have ? 'have' : ''}` },
      h('span', { class: 'label', title: t.name }, t.name),
      h('div', { class: 'bar-track' }, h('div', { class: 'bar-fill', style: `width:${(t.count / max) * 100}%` })),
      h('span', { class: 'count mono' }, fmt(t.count)))));
    const missing = list.filter(t => !t.have).slice(0, 4);
    gaps.replaceChildren(missing.length
      ? h('div', { class: 'callout gap' }, `Najczęstsze braki w Twoim CV: ${missing.map(t => t.name).join(', ')} — ` +
        `każda z nich pojawia się w co najmniej ${fmt(Math.min(...missing.map(t => t.count)))} ofertach.`)
      : h('div', { class: 'callout signal' }, 'Masz w CV wszystkie technologie z tej listy.'));
  };
  drawChart(techAll);

  const segButtons = [['all', 'Wszystkie'], ['junior', 'Junior'], ['mid', 'Mid'], ['senior', 'Senior']].map(([value, label]) =>
    h('button', { type: 'button', class: value === 'all' ? 'on' : '', onclick: async e => {
      segButtons.forEach(b => b.classList.remove('on')); e.currentTarget.classList.add('on');
      drawChart(await api(`/api/stats/technologies?level=${value}&limit=12`));
    } }, label));

  const levelMax = Math.max(...levels.map(l => l.count), 1);
  const shortLevel = name => name.replace(/^.*\((.*)\)$/, '$1').replace(/ \/ .*$/, '').replace(/^\w/, c => c.toUpperCase());

  setPage(
    h('h1', { class: 'brand-title' }, 'JobRadar'),
    h('section', { class: 'hero recap' }, svg(RINGS_SVG),
      h('h2', {}, 'Twój recap'),
      h('p', { class: 'hero-text' }, sentence),
      h('div', { class: 'facts' },
        h('div', { class: 'fact' }, h('div', { class: 'num' }, fmt(summary.junior)), h('div', {}, 'ofert juniorskich')),
        h('div', { class: 'fact' }, h('div', { class: 'num' }, String(profile.commercial_months).replace('.', ',')), h('div', {}, 'mies. stażu komercyjnego')),
        ...haveTop.map(t => h('div', { class: 'fact' }, h('div', { class: 'num' }, `${pct(t.count, summary.with_technologies)}%`), h('div', {}, `ofert z technologią ${t.name}`)))),
      matches
        ? h('div', { class: 'recap-offers' }, h('h3', {}, 'Najlepiej pasują do Ciebie'), h('div', { class: 'offer-list' }, matches.map(o => offerRow(o))))
        : h('div', { class: 'callout gap' }, 'Dopasowanie do CV jest niedostępne. Uruchom LM Studio z modelem bge-m3.'),
      h('p', {}, h('a', { class: 'link', href: '#/oferty?level=junior' }, 'Zobacz wszystkie oferty juniorskie  →'))),
    h('section', { class: 'panel market' },
      h('header', { class: 'page-head' },
        h('h2', { class: 'market-title' }, 'Analiza ogólna rynku'),
        h('div', { class: 'faint small' }, `${fmt(summary.total)} ofert z pracuj.pl · ${fmt(summary.active)} aktywnych · zaktualizowano ${new Date(summary.updated_at).toLocaleString('pl-PL', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })}`)),
      h('div', { class: 'columns' },
        h('div', { class: 'stack' },
          h('div', { class: 'section-head' }, h('h3', {}, 'Najczęściej wymagane technologie'), h('div', { class: 'segmented' }, segButtons)),
          h('div', { class: 'legend' }, h('span', { class: 'have' }, 'masz w CV'), h('span', { class: 'miss' }, 'brakuje Ci')),
          chart, gaps,
          h('div', { class: 'faint tiny' }, `Liczba ofert, w których technologia jest na liście wymaganych · ${fmt(summary.with_technologies)} ofert z podanymi technologiami`)),
        h('div', { class: 'stack-lg' },
          h('div', { class: 'stack' }, h('h3', {}, 'Dla kogo są oferty'),
            ...levels.slice(0, 6).map(l => {
              const mine = /junior/i.test(l.name);
              return meter(shortLevel(l.name) + (mine ? '  ·  Twój poziom' : ''), fmt(l.count), l.count / levelMax, mine ? 'mine' : '');
            })),
          h('div', { class: 'stack' }, h('h3', {}, 'W ofertach juniorskich'),
            h('div', { class: 'tags' }, techJunior.map(t => h('span', { class: `tag ${t.have ? 'have' : ''}` }, t.name, h('span', { class: 'mono' }, t.count)))),
            h('div', { class: 'faint tiny' }, `Wyróżnione masz w CV: ${techJunior.filter(t => t.have).length} z ${techJunior.length}`))))),
  );
}

/* ---------- Oferty ---------- */

const offerState = { q: '', level: 'junior', tech: [], work_mode: '', sort: 'match', active: true };

async function renderOffers(params) {
  if (params.get('level')) offerState.level = params.get('level');
  offerState.q = params.get('q') || '';
  loading();
  const topTech = await api('/api/stats/technologies?limit=14');
  let offset = 0;

  const list = h('div', { class: 'offer-list' });
  const notice = h('div');
  const count = h('span', { class: 'faint small' });
  const more = h('button', { class: 'more', type: 'button', onclick: () => load(false) }, 'Pokaż więcej');

  async function load(reset = true) {
    if (reset) { offset = 0; list.replaceChildren(h('div', { class: 'skeleton', style: 'height:80px;margin-top:12px' })); }
    const qs = new URLSearchParams({ q: offerState.q, level: offerState.level, work_mode: offerState.work_mode,
      sort: offerState.sort, active: offerState.active, limit: 30, offset });
    offerState.tech.forEach(t => qs.append('tech', t));
    try {
      if (offerState.sort === 'match') {
        const params = new URLSearchParams({ level: offerState.level, limit: 50 });
        let items;
        try {
          items = offerState.q.trim()
            ? await api(`/api/search?${params}&q=${encodeURIComponent(offerState.q)}`)
            : await api(`/api/match?${params}`);
        } catch (err) {
          offerState.sort = 'newest';
          sortSelect.value = 'newest';
          notice.replaceChildren(h('div', { class: 'callout gap' },
            'Dopasowanie do CV jest niedostępne — uruchom LM Studio z modelem bge-m3. Na razie pokazuję najnowsze oferty.'));
          return load();
        }
        notice.replaceChildren();
        list.replaceChildren(...items.map(o => offerRow(o)));
        count.textContent = offerState.q.trim()
          ? `${items.length} ofert najbliższych znaczeniowo do „${offerState.q}”`
          : `${items.length} ofert najlepiej pasujących do Twojego CV`;
        more.hidden = true;
        return;
      }
      const data = await api(`/api/offers?${qs}`);
      if (reset) list.replaceChildren();
      count.textContent = `${fmt(data.total)} ofert`;
      if (!data.total) {
        list.replaceChildren(h('div', { class: 'empty' }, svg(RINGS_SVG), h('h2', {}, 'Radar nic nie wykrył'),
          h('p', {}, 'Spróbuj usunąć któryś filtr albo wpisać inne słowo.')));
      }
      data.items.forEach(o => list.append(offerRow(o)));
      offset += data.items.length;
      more.hidden = offset >= data.total;
    } catch (err) {
      list.replaceChildren(h('p', { class: 'error' }, `Błąd: ${err.message}`));
    }
  }

  const select = (options, key) => h('select', { onchange: e => { offerState[key] = e.target.value; load(); } },
    options.map(([value, label]) => h('option', { value, selected: offerState[key] === value }, label)));

  const sortSelect = select([['match', 'Najlepiej dopasowane do CV'], ['newest', 'Najnowsze'], ['expiring', 'Wkrótce wygasają']], 'sort');

  const techButtons = topTech.map(t => h('button', { type: 'button', class: `tag ${t.have ? 'have' : ''} ${offerState.tech.includes(t.name) ? 'on' : ''}`,
    onclick: e => {
      const i = offerState.tech.indexOf(t.name);
      if (i >= 0) offerState.tech.splice(i, 1); else offerState.tech.push(t.name);
      e.currentTarget.classList.toggle('on'); load();
    } }, t.name));

  setPage(
    h('header', { class: 'page-head' }, h('h1', {}, 'Oferty'), count),
    h('div', { class: 'toolbar' },
      h('div', { class: 'filters' },
        select([['all', 'Każdy poziom'], ['junior', 'Junior'], ['mid', 'Mid'], ['senior', 'Senior']], 'level'),
        select([['', 'Każdy tryb pracy'], ['Praca zdalna', 'Zdalnie'], ['Praca hybrydowa', 'Hybrydowo'], ['Praca stacjonarna', 'Stacjonarnie']], 'work_mode'),
        sortSelect,
        h('label', { class: 'check' }, h('input', { type: 'checkbox', checked: offerState.active,
          onchange: e => { offerState.active = e.target.checked; load(); } }), 'tylko aktywne')),
      h('div', { class: 'tags' }, techButtons)),
    notice, list, more,
  );
  load();
}

function offerRow(o) {
  const loc = o.locations?.length ? o.locations[0] + (o.locations.length > 1 ? ` +${o.locations.length - 1}` : '') : null;
  const left = daysLeft(o.expires_at);
  return h('a', { class: 'offer-row', href: `#/oferty/${encodeURIComponent(o.id)}` },
    h('div', {},
      h('h3', {}, o.title),
      h('div', { class: 'offer-meta' }, [o.company, loc, o.work_modes?.[0]].filter(Boolean).join('  ·  ')),
      techTags(o.technologies, 6)),
    h('div', { class: 'offer-side' },
      h('div', {}, o.salary ? h('div', { class: 'salary' }, o.salary) : h('div', { class: 'faint small' }, 'widełki nie podane'),
        left != null ? h('div', { class: 'expires' }, left > 0 ? `ważna jeszcze ${left} dni` : 'wygasła') : null,
        o.analysis_score != null ? h('div', { class: 'match-badge' }, `analiza AI: ${o.analysis_score}/100`)
          : o.match != null ? h('div', { class: 'expires' }, `podobieństwo do CV: ${o.match}%`) : null),
      ring(o.coverage.have, o.coverage.total)));
}

/* ---------- Szczegóły oferty ---------- */

const STATUS_LABEL = { met: 'spełnione', partial: 'częściowo', missing: 'brak w CV' };

function requirementList(items, checks) {
  return h('div', { class: 'req-list' }, items.map((text, i) => {
    const c = checks?.find(x => x.id === i + 1);
    return h('div', { class: `req ${c ? c.status : ''}` }, h('span', { class: 'dot', title: c ? STATUS_LABEL[c.status] : '' }),
      h('div', {}, h('div', {}, text),
        c && c.status !== 'missing' && c.evidence ? h('div', { class: 'evidence' }, `„${c.evidence}”`) : null,
        c && c.status === 'missing' ? h('div', { class: 'gap-note' }, 'Brak w CV') : null));
  }));
}

function countStatus(checks) {
  return { met: checks.filter(c => c.status === 'met').length, partial: checks.filter(c => c.status === 'partial').length, total: checks.length };
}

async function renderOffer(id) {
  loading();
  const [o, analysis] = await Promise.all([
    api(`/api/offers/${encodeURIComponent(id)}`),
    api(`/api/offers/${encodeURIComponent(id)}/analysis`).catch(() => null),
  ]);
  const r = analysis?.result;
  const cov = o.coverage;
  const ratio = cov.total ? cov.have / cov.total : 0;
  const missing = o.technologies.filter(t => !t.have).map(t => t.name);
  const left = daysLeft(o.expires_at);

  const analyseButton = (label, cls = 'btn primary') => h('button', { class: cls, type: 'button', onclick: async e => {
    const btn = e.currentTarget;
    btn.disabled = true; btn.textContent = 'Gemma analizuje ofertę… (ok. 15 s)';
    try {
      await fetch(`/api/offers/${encodeURIComponent(id)}/analysis?force=${analysis ? 'true' : 'false'}`, { method: 'POST' })
        .then(res => res.ok ? res.json() : res.json().then(b => Promise.reject(new Error(b.detail || res.statusText))));
      renderOffer(id);
    } catch (err) {
      btn.disabled = false; btn.textContent = label;
      btn.after(h('p', { class: 'error small' }, err.message));
    }
  } }, label);

  let hero;
  if (r) {
    const req = countStatus(r.requirements);
    const nice = countStatus(r.nice_to_have);
    hero = h('section', { class: 'hero match' }, svg(RINGS_SVG),
      h('div', {},
        h('div', { class: 'score' }, h('span', { class: 'num' }, analysis.score), h('span', { class: 'of' }, '/100')),
        h('div', { class: 'muted small' }, 'dopasowanie do Twojego CV')),
      h('div', { class: 'vline' }),
      h('div', {},
        h('div', { class: 'eyebrow' }, 'W skrócie'),
        h('p', { class: 'summary-text' }, r.summary),
        h('p', { class: 'faint tiny' }, `Analiza: ${analysis.model}, lokalnie · ${new Date(analysis.created_at).toLocaleDateString('pl-PL')} · ${(analysis.duration_ms / 1000).toFixed(1)} s` +
          (analysis.flags.length ? ` · do sprawdzenia: ${analysis.flags.join(', ')}` : ''))),
      h('div', { class: 'stack' },
        meter('Wymagania', `${req.met}${req.partial ? ` (+${req.partial})` : ''} z ${req.total}`, req.total ? (req.met + req.partial / 2) / req.total : 0, (req.met + req.partial / 2) / Math.max(req.total, 1) >= 0.5 ? 'good' : 'gap'),
        nice.total ? meter('Mile widziane', `${nice.met}${nice.partial ? ` (+${nice.partial})` : ''} z ${nice.total}`, (nice.met + nice.partial / 2) / nice.total, 'good') : null,
        r.required_months ? meter('Staż komercyjny', `${String(r.months).replace('.', ',')} z ${r.required_months} mies.`, Math.min(r.months / r.required_months, 1), r.months >= r.required_months ? 'good' : 'gap') : null));
  } else {
    hero = h('section', { class: 'hero match' }, svg(RINGS_SVG),
      h('div', {},
        h('div', { class: 'score' }, h('span', { class: 'num' }, cov.total ? Math.round(ratio * 100) : '–'), h('span', { class: 'of' }, '%')),
        h('div', { class: 'muted small' }, 'pokrycia technologii z Twojego CV')),
      h('div', { class: 'vline' }),
      h('div', {},
        h('div', { class: 'eyebrow' }, 'W skrócie'),
        h('p', { class: 'summary-text' }, cov.total
          ? `Masz ${cov.have} z ${cov.total} technologii wymaganych w tej ofercie.` + (missing.length ? ` Brakuje Ci: ${missing.join(', ')}.` : '')
          : 'Ta oferta nie podaje listy technologii.'),
        o.requirements?.length ? analyseButton('Przeanalizuj wymagania z Gemmą', 'btn') : null),
      h('div', { class: 'stack' },
        meter('Technologie', `${cov.have} z ${cov.total}`, ratio, ratio >= 0.5 ? 'good' : 'gap'),
        left != null ? meter('Ważna jeszcze', `${Math.max(left, 0)} dni`, Math.min(Math.max(left, 0) / 30, 1), left > 7 ? 'good' : 'gap') : null));
  }

  const sections = [];
  if (!o.details_fetched_at) {
    sections.push(h('div', { class: 'callout signal' }, 'Szczegóły tej oferty jeszcze się pobierają — scraper do niej wróci.'));
  }
  if (o.requirements?.length) {
    const req = r ? countStatus(r.requirements) : null;
    sections.push(h('section', { class: 'stack' },
      h('div', { class: 'section-head' }, h('h2', {}, 'Wymagania'),
        h('span', { class: 'meta' }, req ? `${req.met} z ${req.total} potwierdzonych w CV` : `${o.requirements.length} punktów`)),
      requirementList(o.requirements, r?.requirements)));
  }
  if (o.nice_to_have?.length) sections.push(h('section', { class: 'stack' }, h('h2', {}, 'Mile widziane'), requirementList(o.nice_to_have, r?.nice_to_have)));
  if (o.responsibilities?.length) sections.push(h('section', { class: 'stack' }, h('h2', {}, 'Zakres obowiązków'),
    o.responsibilities.map(text => h('div', { class: 'duty' }, text))));
  if (o.about_project) sections.push(h('section', { class: 'stack' }, h('h2', {}, 'O projekcie'), h('p', { class: 'prose' }, o.about_project)));

  const tips = r?.cv_tips?.length ? r.cv_tips : [
    missing.length ? `Sprawdź, czy masz choć podstawy: ${missing.slice(0, 3).join(', ')} — jeśli tak, dopisz je do CV.` : null,
    'Dopasuj opis projektu JobRadar do słów kluczowych z wymagań tej oferty.',
    'Przeczytaj „Mile widziane” — każdy spełniony punkt warto wyeksponować.',
  ].filter(Boolean);

  setPage(
    h('a', { class: 'breadcrumb', href: '#/oferty' }, '← Oferty'),
    h('header', { class: 'detail-head' },
      h('div', { class: 'page-head' },
        h('h1', {}, o.title),
        h('div', { class: 'muted' }, [o.company, o.locations?.join(', '), o.work_modes?.join(', '), o.contracts?.join(', ')].filter(Boolean).join('  ·  ')),
        h('div', { class: 'faint small' }, [o.salary, o.expires_at && `ważna do ${date(o.expires_at)}`, !o.is_active && 'oferta nieaktywna'].filter(Boolean).join('  ·  '))),
      h('div', { class: 'actions' }, o.url ? h('a', { class: 'btn', href: o.url, target: '_blank', rel: 'noopener noreferrer' }, 'Otwórz na pracuj.pl ↗') : null)),
    hero,
    h('div', { class: 'columns' },
      h('div', { class: 'stack-lg' }, sections.length ? sections : h('p', { class: 'muted' }, 'Brak szczegółów oferty.')),
      h('aside', { class: 'stack-lg' },
        h('div', { class: 'todo' },
          h('h3', {}, 'Zanim wyślesz CV'),
          h('ol', {}, tips.map(t => h('li', {}, t))),
          r ? analyseButton('Przeanalizuj ponownie', 'btn') : h('button', { class: 'btn primary', type: 'button', disabled: true, title: 'Wkrótce' }, 'Przygotuj aplikację')),
        o.technologies.length ? h('section', { class: 'stack' }, h('h3', {}, 'Technologie w ofercie'), techTags(o.technologies),
          h('div', { class: 'faint tiny' }, 'Wyróżnione masz w CV')) : null,
        o.technologies_optional.length ? h('section', { class: 'stack' }, h('h3', {}, 'Mile widziane technologie'), techTags(o.technologies_optional)) : null,
        o.benefits?.length ? h('section', { class: 'stack' }, h('h3', {}, 'Benefity'), h('div', { class: 'tags' }, o.benefits.map(b => tag(b)))) : null,
        o.recruitment_stages?.length ? h('section', { class: 'stack' }, h('h3', {}, 'Etapy rekrutacji'),
          h('div', { class: 'tags' }, o.recruitment_stages.map((s, i) => tag(`${i + 1}. ${s}`)))) : null)),
  );
}

/* ---------- JobBro (agent AI, na razie sam wygląd) ---------- */

function renderJobBro() {
  setPage(
    h('header', { class: 'page-head' }, h('h1', {}, 'JobBro'), h('div', { class: 'muted' }, 'Twój agent AI do szukania pracy')),
    h('section', { class: 'hero jobbro' }, svg(RINGS_SVG),
      h('p', { class: 'hero-text' }, 'JobBro będzie pomagać przygotować aplikację i pilnować odpowiedzi od firm.'),
      h('form', { class: 'jobbro-input', onsubmit: e => e.preventDefault() },
        h('input', { class: 'search', type: 'text', disabled: true, placeholder: 'Napisz do JobBro…', 'aria-label': 'Wiadomość do JobBro' }),
        h('button', { class: 'btn', type: 'submit', disabled: true }, 'Wyślij')),
      h('p', { class: 'faint small' }, 'Agent nie jest jeszcze podłączony.')),
  );
}

/* ---------- Moje aplikacje ---------- */

function renderApps() {
  const cols = ['Zaaplikowano', 'Rozmowa', 'Zadanie', 'Oferta', 'Odrzucono'];
  setPage(
    h('header', { class: 'page-head' }, h('h1', {}, 'Moje aplikacje'),
      h('div', { class: 'faint small' }, 'Statusy będą aktualizować się same na podstawie maili rekrutacyjnych')),
    h('div', { class: 'kanban' }, cols.map(c => h('div', { class: 'kanban-col' }, h('h3', {}, c, h('span', { class: 'mono faint' }, '0'))))),
    h('div', { class: 'empty' }, svg(RINGS_SVG), h('h2', {}, 'Jeszcze nic tu nie ma'),
      h('p', {}, 'Kiedy zaaplikujesz na ofertę, pojawi się w pierwszej kolumnie. JobRadar przypomni Ci o follow-upie, jeśli firma długo milczy.'),
      h('p', {}, h('a', { class: 'link', href: '#/oferty' }, 'Przejdź do ofert  →'))),
  );
}

/* ---------- Mój profil ---------- */

async function renderProfile() {
  loading();
  const p = await api('/api/profile');
  const period = e => `${date(e.start)} – ${e.end ? date(e.end) : 'obecnie'}`;
  const kindLabel = { job: 'praca', internship: 'staż', organization: 'organizacja' };
  setPage(
    h('header', { class: 'page-head' }, h('h1', {}, p.name), h('div', { class: 'muted' }, p.headline)),
    h('section', { class: 'hero' }, svg(RINGS_SVG),
      h('div', { class: 'eyebrow' }, 'Staż komercyjny'),
      h('div', { class: 'score' }, h('span', { class: 'num' }, String(p.commercial_months).replace('.', ',')), h('span', { class: 'of' }, 'mies.')),
      h('p', { class: 'muted small' }, 'Liczone z pracy i staży, bez organizacji studenckich. Nakładające się okresy liczą się raz.')),
    h('div', { class: 'columns' },
      h('section', { class: 'stack' }, h('h2', {}, 'Doświadczenie'),
        h('div', { class: 'timeline' }, p.experience.map(e => h('div', { class: 'tl-item' },
          h('div', { class: 'mono faint' }, period(e)),
          h('div', {}, h('div', {}, h('strong', {}, e.title)), h('div', { class: 'muted small' }, `${e.company} · ${kindLabel[e.kind]}`)))))),
      h('aside', { class: 'stack' }, h('h2', {}, 'Umiejętności'), h('div', { class: 'tags' }, p.skills.map(s => tag(s, 'have'))),
        h('div', { class: 'faint tiny' }, 'Na razie z pliku user/profile.py. W kolejnej wersji będą wyciągane z CV przez Gemmę.'))),
  );
}

/* ---------- router & theme ---------- */

async function route() {
  const [path, query = ''] = location.hash.replace(/^#/, '').split('?');
  const params = new URLSearchParams(query);
  const parts = path.split('/').filter(Boolean);
  const name = parts[0] === 'oferty' ? 'offers' : parts[0] === 'aplikacje' ? 'apps' : parts[0] === 'profil' ? 'profile' : parts[0] === 'jobbro' ? 'jobbro' : 'market';
  document.querySelectorAll('[data-route]').forEach(a => a.classList.toggle('active', a.dataset.route === name));
  document.getElementById('topsearch-input').value = name === 'offers' && !parts[1] ? (params.get('q') || '') : '';
  try {
    if (name === 'offers' && parts[1]) await renderOffer(decodeURIComponent(parts[1]));
    else if (name === 'offers') await renderOffers(params);
    else if (name === 'jobbro') renderJobBro();
    else if (name === 'apps') renderApps();
    else if (name === 'profile') await renderProfile();
    else await renderMarket();
  } catch (err) {
    failed(err);
  }
}

const toggle = document.getElementById('theme-toggle');
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  toggle.textContent = theme === 'dark' ? 'Tryb jasny' : 'Tryb ciemny';
}
let savedTheme = 'dark';
try { savedTheme = localStorage.getItem('jobradar-theme') || 'dark'; } catch { /* brak dostępu do localStorage */ }
applyTheme(savedTheme);
toggle.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem('jobradar-theme', next); } catch { /* ignoruj */ }
});

document.getElementById('topsearch').addEventListener('submit', e => {
  e.preventDefault();
  const q = document.getElementById('topsearch-input').value.trim();
  const target = q ? `#/oferty?q=${encodeURIComponent(q)}` : '#/oferty';
  if (location.hash === target) route(); else location.hash = target;
});

window.addEventListener('hashchange', route);
route();
