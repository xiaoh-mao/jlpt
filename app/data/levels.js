// 各级别的考试结构（2010 年新制，公式問題集 2012/2018 都是这一版）。
// parts：卷子拆成 V 文字・語彙 / G 文法 / R 読解 / L 聴解 四块，每块对应官方一个 PDF；
//   sec 是正答表里的小标题（build_keys.py 的 SEC），from/to 是 問題 编号范围。
// booklets：模考时真实的考试科目和时限（分钟），官网 testsections.html。
// scores：得点区分和基准点，官网 results.html；分数只能按正确率线性估算（真考试是等化计分）。
window.JLPT_LEVELS = {
  N1: {
    name: 'N1', pass: 100,
    parts: { V: { sec: 'lang', from: 1, to: 4 }, G: { sec: 'lang', from: 5, to: 7 }, R: { sec: 'lang', from: 8, to: 99 }, L: { sec: 'listen' } },
    booklets: [
      { name: '言語知識（文字・語彙・文法）・読解', parts: ['V', 'G', 'R'], min: 110 },
      { name: '聴解', parts: ['L'], min: 55 },
    ],
    scores: [
      { name: '言語知識（文字・語彙・文法）', parts: ['V', 'G'], max: 60, min: 19 },
      { name: '読解', parts: ['R'], max: 60, min: 19 },
      { name: '聴解', parts: ['L'], max: 60, min: 19 },
    ],
    types: {
      lang: ['漢字読み', '文脈規定', '言い換え類義', '用法', '文法形式の判断', '文の組み立て', '文章の文法',
        '内容理解（短文）', '内容理解（中文）', '内容理解（長文）', '統合理解', '主張理解（長文）', '情報検索'],
      listen: ['課題理解', 'ポイント理解', '概要理解', '即時応答', '統合理解'],
    },
  },
  N2: {
    name: 'N2', pass: 90,
    parts: { V: { sec: 'lang', from: 1, to: 6 }, G: { sec: 'lang', from: 7, to: 9 }, R: { sec: 'lang', from: 10, to: 99 }, L: { sec: 'listen' } },
    booklets: [
      { name: '言語知識（文字・語彙・文法）・読解', parts: ['V', 'G', 'R'], min: 105 },
      { name: '聴解', parts: ['L'], min: 50 },
    ],
    scores: [
      { name: '言語知識（文字・語彙・文法）', parts: ['V', 'G'], max: 60, min: 19 },
      { name: '読解', parts: ['R'], max: 60, min: 19 },
      { name: '聴解', parts: ['L'], max: 60, min: 19 },
    ],
    types: {
      lang: ['漢字読み', '表記', '語形成', '文脈規定', '言い換え類義', '用法', '文法形式の判断', '文の組み立て', '文章の文法',
        '内容理解（短文）', '内容理解（中文）', '統合理解', '主張理解（長文）', '情報検索'],
      listen: ['課題理解', 'ポイント理解', '概要理解', '即時応答', '統合理解'],
    },
  },
  N3: {
    name: 'N3', pass: 95,
    parts: { V: { sec: 'vocab', from: 1, to: 99 }, G: { sec: 'gram', from: 1, to: 3 }, R: { sec: 'gram', from: 4, to: 99 }, L: { sec: 'listen' } },
    booklets: [
      { name: '言語知識（文字・語彙）', parts: ['V'], min: 30 },
      { name: '言語知識（文法）・読解', parts: ['G', 'R'], min: 70 },
      { name: '聴解', parts: ['L'], min: 40 },
    ],
    scores: [
      { name: '言語知識（文字・語彙・文法）', parts: ['V', 'G'], max: 60, min: 19 },
      { name: '読解', parts: ['R'], max: 60, min: 19 },
      { name: '聴解', parts: ['L'], max: 60, min: 19 },
    ],
    types: {
      vocab: ['漢字読み', '表記', '文脈規定', '言い換え類義', '用法'],
      gram: ['文法形式の判断', '文の組み立て', '文章の文法', '内容理解（短文）', '内容理解（中文）', '内容理解（長文）', '情報検索'],
      listen: ['課題理解', 'ポイント理解', '概要理解', '発話表現', '即時応答'],
    },
  },
  N4: {
    name: 'N4', pass: 90,
    parts: { V: { sec: 'vocab', from: 1, to: 99 }, G: { sec: 'gram', from: 1, to: 3 }, R: { sec: 'gram', from: 4, to: 99 }, L: { sec: 'listen' } },
    booklets: [
      { name: '言語知識（文字・語彙）', parts: ['V'], min: 25 },
      { name: '言語知識（文法）・読解', parts: ['G', 'R'], min: 55 },
      { name: '聴解', parts: ['L'], min: 35 },
    ],
    scores: [
      { name: '言語知識（文字・語彙・文法）・読解', parts: ['V', 'G', 'R'], max: 120, min: 38 },
      { name: '聴解', parts: ['L'], max: 60, min: 19 },
    ],
    types: {
      vocab: ['漢字読み', '表記', '文脈規定', '言い換え類義', '用法'],
      gram: ['文法形式の判断', '文の組み立て', '文章の文法', '内容理解（短文）', '内容理解（中文）', '情報検索'],
      listen: ['課題理解', 'ポイント理解', '発話表現', '即時応答'],
    },
  },
  N5: {
    name: 'N5', pass: 80,
    parts: { V: { sec: 'vocab', from: 1, to: 99 }, G: { sec: 'gram', from: 1, to: 3 }, R: { sec: 'gram', from: 4, to: 99 }, L: { sec: 'listen' } },
    booklets: [
      { name: '言語知識（文字・語彙）', parts: ['V'], min: 20 },
      { name: '言語知識（文法）・読解', parts: ['G', 'R'], min: 40 },
      { name: '聴解', parts: ['L'], min: 30 },
    ],
    scores: [
      { name: '言語知識（文字・語彙・文法）・読解', parts: ['V', 'G', 'R'], max: 120, min: 38 },
      { name: '聴解', parts: ['L'], max: 60, min: 19 },
    ],
    types: {
      vocab: ['漢字読み', '表記', '文脈規定', '言い換え類義'],
      gram: ['文法形式の判断', '文の組み立て', '文章の文法', '内容理解（短文）', '内容理解（中文）', '情報検索'],
      listen: ['課題理解', 'ポイント理解', '発話表現', '即時応答'],
    },
  },
};

window.JLPT_PART_NAMES = { V: '文字・語彙', G: '文法', R: '読解', L: '聴解' };

// 官方两套。文件名是 jlpt.jp 原样：N2V.pdf / N2Q1.mp3 …
window.JLPT_VOLS = {
  2018: { title: '公式問題集 第二集', year: 2018 },
  2012: { title: '公式問題集', year: 2012 },
};
