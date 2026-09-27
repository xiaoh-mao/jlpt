'use strict';
/* JLPT 做题 —— 考试适配（界面和做法全在 core.js，两个 app 共用）。这里只有 JLPT 自己的：
   官方卷：答案 data/keys.js（脚本从正答表生成），每题在卷子/听力原文里的位置和录音里的秒数 data/tests.js，
   听力原文的中文译文 data/trans.js，考试结构和合格线 data/levels.js；
   自备卷：papers/自备/<名字>/ 下的 PDF + MP3 + test.json（答案），用「导入自备试卷」设置，卷子用 PDF 原样显示。
   算分：得点区分按正确率线性估算（真考试是等化计分）。 */

const LV = window.JLPT_LEVELS;
const PN = window.JLPT_PART_NAMES;
const PART_ORDER = ['V', 'G', 'R', 'L'];
const DOCS = [...PART_ORDER, 'script', 'answer'];   // 一套卷子的各份文件

const labText = l => { const [a, b] = String(l).split('-'); return b ? `${a}(${b})` : a; };   // 小问 3-1 -> 3(1)
function partOf(level, sec, m) {
  const parts = LV[level].parts;
  for (const p of PART_ORDER) {
    const d = parts[p];
    if (d.sec === sec && (d.from == null || (m >= d.from && m <= d.to))) return p;
  }
  return null;
}

// t：{ id, level, order, title, sub, tag, files:{卷子:PDF}, audio:{問題号:MP3}, secs（keys.js 那样的答案）, pages, img, trans }
function addJlpt(t) {
  const P = t.pages, types = LV[t.level].types;
  const raw = [];
  for (const sec of Object.keys(t.secs)) {
    for (const g of t.secs[sec]) {
      for (const [label, ans] of g.items) {
        const part = partOf(t.level, sec, g.m);
        if (part) raw.push({ sec, m: g.m, label: String(label), ans, part });
      }
    }
  }
  raw.sort((a, b) => PART_ORDER.indexOf(a.part) - PART_ORDER.indexOf(b.part));   // 稳定排序，部分内保持原顺序
  const audio = [], groups = [], items = [], grps = {};
  for (const r of raw) {
    const gk = `${r.sec}:${r.m}`;
    let g = grps[gk];
    if (!g) {
      const name = (types[r.sec] || [])[r.m - 1] || '';
      const gp = P?.g[gk], sg = P?.sg[gk];
      g = grps[gk] = { key: gk, part: r.part, label: `問題 ${r.m}`, name, pos: gp ? [...gp, 1] : null, spos: sg ? ['script', ...sg, 1] : null,
        nOpt: /即時応答|発話表現/.test(name) ? 3 : 4, track: null };
      if (r.part === 'L' && t.audio[r.m]) { g.track = audio.length; audio.push({ url: t.audio[r.m], name: `問題${r.m}` }); }   // 每个問題一段录音
      groups.push(g);
    }
    const key = `${gk}:${r.label}`;
    const pos = P?.q[key] || null, s = P?.s[key];
    const it = {
      key, part: r.part, grp: g, label: labText(r.label), long: `問題 ${r.m} · 第 ${labText(r.label)} 题`, ans: r.ans, nOpt: g.nOpt,
      pos, nopick: !!pos && pos[3] === 0,             // 卷上没有单独位置的题（用的大题标题位置），点卷子时不认
      spos: s ? ['script', ...s, 1] : null, track: g.track, cue: P?.cue[key] ?? null,
      qid: key.replace(/-\d+$/, ''), say: `${labText(r.label.split('-')[0])}番`,
    };
    it.tip = P ? `卷子${it.cue != null ? '和录音' : ''}跳到这题${pos && !pos[3] ? '（这题卷上没有单独的位置，跳到大题）' : ''}` : '';
    items.push(it);
  }
  addTest({
    id: t.id, level: t.level, order: t.order, title: t.title, sub: t.sub, tag: t.tag, short: t.tag, custom: t.custom,
    parts: PART_ORDER.filter(p => items.some(i => i.part === p)), partName: PN, partDoc: { V: 'V', G: 'G', R: 'R', L: 'L' },
    docs: P?.docs || null, img: t.img, files: t.files, audio, groups, items,
    // 译文一题一段；q 是题号或「例」
    trans: t.trans?.map(x => ({
      at: x.at, head: `問題${x.m} ${x.q === '例' ? '例' : x.q + '番'}`, lines: x.lines,
      key: x.q === '例' ? '' : items.find(it => it.key === `listen:${x.m}:${x.q}` || it.key.startsWith(`listen:${x.m}:${x.q}-`))?.key || '',
    })) || null,
  });
}

function loadOfficial() {
  for (const [id, secs] of Object.entries(window.JLPT_KEYS)) {
    const [vol, level] = id.split('-');
    const base = `/papers/${vol}/${level}`;
    const audio = {};
    for (const g of secs.listen || []) audio[g.m] = `${base}Q${g.m}.mp3`;
    addJlpt({
      id, level, order: +vol, title: window.JLPT_VOLS[vol].title, sub: `${vol} 年 · 官方`, tag: vol,
      files: Object.fromEntries(DOCS.map(d => [d, `${base}${d}.pdf`])), audio,
      secs, pages: window.JLPT_TESTS?.[id] || null, img: `/papers/${vol}/img/${level}`, trans: window.JLPT_TRANS?.[id] || null,
    });
  }
}

// 自备试卷：papers/自备/<名字>/test.json
async function loadCustom() {
  let list = [];
  try { list = await api('/api/custom'); } catch { return []; }
  for (const id of Object.keys(TESTS)) if (TESTS[id].custom) delete TESTS[id];
  for (const c of list) {
    if (!c.test) continue;
    try {
      const j = JSON.parse(c.test);
      const base = `/papers/${encodeURIComponent('自备')}/${encodeURIComponent(c.name)}/`;
      const f = u => (u ? base + encodeURIComponent(u) : '');
      const audio = {};
      (j.audio || []).forEach((u, i) => { if (u) audio[i + 1] = f(u); });
      addJlpt({
        id: 'custom-' + c.name, level: j.level, order: 0, custom: c.name, title: j.title || c.name, sub: '自备', tag: '自备',
        files: Object.fromEntries(DOCS.map(d => [d, f(j.files?.[d])])), audio, secs: j.secs,
      });
    } catch (e) { console.warn('自备试卷读不了', c.name, e); }
  }
  return list;
}

// 得点区分：只有这一区的题全做了才给 0–60（或 0–120）的估算分，不全就只报正确率
function score(test, set, answers) {
  const lv = LV[test.level];
  const areas = lv.scores.map(s => {
    const all = test.items.filter(i => s.parts.includes(i.part));
    const done = all.filter(i => set.has(i.key));
    let ok = 0;
    for (const it of done) if (answers[it.key] === it.ans) ok++;
    const full = done.length === all.length && all.length > 0;
    return { name: s.name, ok, n: done.length, max: s.max, min: s.min, full, score: full ? Math.round(ok / done.length * s.max) : null };
  }).filter(a => a.n);
  const max = lv.scores.reduce((s, a) => s + a.max, 0);
  const full = areas.length === lv.scores.length && areas.every(a => a.full);
  const total = full ? areas.reduce((s, a) => s + a.score, 0) : null;
  const pass = full ? total >= lv.pass && areas.every(a => a.score >= a.min) : null;
  return {
    areas, full, total, max, pass, label: pass ? '合格' : '不合格', totalName: '估算总分',
    verdict: `${pass ? '✓ 估计合格' : '✗ 未达合格'}（合格线 ${lv.pass}）`,
    note: full ? `每个得点区分按正确率线性折算，竖线是基准点（${lv.scores.map(s => s.min).join(' / ')} 分），任何一科低于它就算总分够也不合格。
      真考试是等化计分（每道题分值不同、按难度调整），这里只能估个大概。` : `分项练习只算正确率；做整套模考才会估算 0–${max} 的分数和合不合格。`,
  };
}

Object.assign(EXAM, {
  name: 'JLPT 做题', lang: 'ja', levels: LV, defaultLevel: 'N2',
  docNames: { ...PN, script: '听力原文', answer: '正答表' },
  typesInTl: true,
  brand: '<span>日本語能力試験 · 官方公式問題集</span>',
  homeTools: '<button class="btn ghost" data-act="import">＋ 导入自备试卷</button>',
  srcNote: `试卷、听力音频、正答表均来自国际交流基金 / 日本国际教育支援协会在
    <a href="https://www.jlpt.jp/samples/sampleindex.html" target="_blank">jlpt.jp</a> 免费公开的《日本語能力試験公式問題集》，每级两套，均选自 2010 年以后的真题。
    分数是按正确率线性估算的，真考试用等化计分，仅供参考。`,
  levelInfo: lv => `满分 ${lv.scores.reduce((s, a) => s + a.max, 0)} · 合格线 ${lv.pass}，各得点区分基准点 ${lv.scores.map(s => s.min).join(' / ')}`,
  load: async () => { loadOfficial(); await loadCustom(); },
  score,
});

// ---------------------------------------------------------------- 导入自备试卷
const SECS_OF = level => (['N1', 'N2'].includes(level) ? ['lang', 'listen'] : ['vocab', 'gram', 'listen']);
const SEC_NAME = { lang: '言語知識（文字・語彙・文法）・読解', vocab: '言語知識（文字・語彙）', gram: '言語知識（文法）・読解', listen: '聴解' };

async function openImport() {
  const list = await loadCustom();
  const rows = list.map(c => `<div class="imp-row"><div class="grow"><b>${esc(c.name)}</b><br><small>${c.files.length} 个文件${c.test ? ' · 已设置答案' : ' · 还没设置答案'}</small></div>
    <button class="btn sm" data-v="edit:${esc(c.name)}">${c.test ? '修改' : '设置答案'}</button></div>`).join('');
  const v = await modal(`<h3>导入自备试卷</h3>
    <p>自己买的或别处合法得到的卷子，也能在这里做：</p>
    <p>1. 在 <b>papers\\自备\\</b> 下建一个文件夹（名字就是卷子名），把 PDF 和听力 MP3 放进去；<br>
       2. 回到这里点「刷新」，再给它设置级别、文件和答案。</p>
    <div class="imp-list">${rows || '<div class="empty">papers\\自备\\ 里还没有文件夹。</div>'}</div>
    <div class="acts"><button class="btn" data-v="folder">打开 自备 文件夹</button><button class="btn" data-v="refresh">刷新</button><button class="btn primary" data-v="close">关闭</button></div>`, { wide: true });
  if (v === 'folder') { await api('/api/open-folder').catch(() => {}); return openImport(); }
  if (v === 'refresh') return openImport();
  if (v && v.startsWith('edit:')) return editCustom(list.find(c => c.name === v.slice(5)));
  renderHome();
}

function secToText(groups) { return (groups || []).map(g => g.items.map(x => x[1]).join('')).join('\n'); }

async function editCustom(c, err = '', draft = null) {
  let j = draft;
  if (!j) { try { j = c.test ? JSON.parse(c.test) : null; } catch { j = null; } }
  j ||= { level: REC.prefs.level, title: c.name, files: {}, audio: [], secs: {} };
  const pdfs = c.files.filter(f => /\.pdf$/i.test(f));
  const mp3s = c.files.filter(f => !/\.pdf$/i.test(f));
  const sel = (id, val) => `<select data-f="${id}"><option value="">（没有）</option>${pdfs.map(f => `<option ${f === val ? 'selected' : ''}>${esc(f)}</option>`).join('')}</select>`;
  const secs = SECS_OF(j.level);
  const v = await modal(`<h3>设置：${esc(c.name)}</h3>
    <div class="form" id="cf">
      <label>级别</label><select data-f="level">${Object.keys(LV).map(l => `<option ${l === j.level ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <label>名称</label><input type="text" data-f="title" value="${esc(j.title)}">
      ${PART_ORDER.map(p => `<label>${tl(PN[p])} PDF</label>${sel(p, j.files[p])}`).join('')}
      <label>听力原文 PDF</label>${sel('script', j.files.script)}
      <label>正答表 PDF</label>${sel('answer', j.files.answer)}
      <label>听力音频</label><div class="audio-order">${mp3s.length ? mp3s.map(f => `<label><input type="checkbox" data-mp3="${esc(f)}" ${j.audio.includes(f) ? 'checked' : ''}> ${esc(f)}</label>`).join('') : '<span class="muted">文件夹里没有音频</span>'}
        <span class="help">按文件名顺序对应 問題1、問題2……（每个 問題 一段音频）</span></div>
      <div class="full help">答案：<b>一行一个「問題」</b>，把该大题每道小题的正确选项连着写，例如 <code>312243</code>。不写「例」。
        全卷一个 PDF 也行，几个部分选同一个文件就好。</div>
      ${secs.map(s => `<label>${tl(SEC_NAME[s])}</label><textarea data-sec="${s}" placeholder="问题1\n问题2\n…">${esc(secToText(j.secs[s]))}</textarea>`).join('')}
    </div>
    ${err ? `<div class="err">${esc(err)}</div>` : ''}
    <div class="acts"><button class="btn" data-v="cancel">取消</button><button class="btn primary" data-v="save">保存</button></div>`, { wide: true });
  if (v !== 'save' && v !== 'relevel') return openImport();
  const res = buildCustom(editCustom.snap);
  if (v === 'relevel') return editCustom(c, '', res.draft || res.test);
  if (res.err) return editCustom(c, res.err, res.draft);
  await api('/api/custom?name=' + encodeURIComponent(c.name), JSON.stringify(res.test));
  await loadCustom();
  toast('已保存：' + res.test.title);
  REC.prefs.level = res.test.level;
  saveRec();
  return openImport();
}
// modal 一关 DOM 就清了，所以点「保存」/ 换级别的那一刻先把表单读出来
function snapForm() {
  const f = {};
  for (const el of $$('#cf [data-f]')) f[el.dataset.f] = el.value;
  f.audio = $$('#cf [data-mp3]').filter(x => x.checked).map(x => x.dataset.mp3);
  f.secs = {};
  for (const el of $$('#cf [data-sec]')) f.secs[el.dataset.sec] = el.value;
  editCustom.snap = f;
}
document.addEventListener('click', e => { if (e.target.closest('#modal [data-v="save"]') && $('#cf')) snapForm(); }, true);
document.addEventListener('change', e => { if (e.target.matches?.('#cf [data-f="level"]')) { snapForm(); modal.close('relevel'); } });
document.addEventListener('click', e => { if (e.target.closest('[data-act="import"]')) openImport(); });

function buildCustom(f) {
  const test = { level: f.level, title: f.title.trim() || '自备试卷', files: {}, audio: f.audio, secs: {} };
  for (const k of DOCS) if (f[k]) test.files[k] = f[k];
  const draft = { ...test, secs: {} };
  const errs = [];
  for (const [sec, text] of Object.entries(f.secs)) {
    const lines = text.split(/\r?\n/).map(s => s.replace(/[\s,，、]/g, '').replace(/[１-４]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))).filter(Boolean);
    let no = 0;
    const groups = [];
    lines.forEach((ln, i) => {
      if (!/^[1-4]+$/.test(ln)) { errs.push(`${SEC_NAME[sec]} 第 ${i + 1} 行只能是 1–4 的数字：${ln}`); return; }
      const items = [...ln].map((c, j) => [String(sec === 'listen' ? j + 1 : ++no), +c]);
      groups.push({ m: i + 1, items });
    });
    if (groups.length) test.secs[sec] = groups;
    draft.secs[sec] = groups;
  }
  if (!Object.keys(test.secs).length) errs.push('至少要填一个部分的答案。');
  return errs.length ? { err: errs.join('\n'), draft } : { test };
}
