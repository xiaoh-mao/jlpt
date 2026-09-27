#!/bin/sh
# 从 jlpt.jp 下《公式問題集》2012/2018 全部文件到 papers/<卷>/，已下好且完整的跳过。
# sample2017/mp3/*Q2.mp3 是官方给 2012 卷换过的问题2音频，归到 2012。
cd "$(dirname "$0")/.." || exit 1
fetch() {
  p="$1"; vol=$(echo "$p" | cut -d/ -f1 | sed 's/sample//; s/2017/2012/'); f=$(basename "$p")
  out="papers/$vol/$f"; mkdir -p "papers/$vol"
  # jlpt.jp 偶尔回 160 字节的坏响应（HEAD 也会，不能靠 Content-Length），所以按内容校验、不对就重下
  ok() { case "$f" in
      *.pdf) head -c4 "$out" 2>/dev/null | grep -q '%PDF' && tail -c1024 "$out" | grep -q '%%EOF' ;;
      *.mp3) [ "$(wc -c < "$out" 2>/dev/null || echo 0)" -gt 200000 ] ;; esac; }
  ok && { echo "skip $out"; return; }
  for i in 1 2 3 4 5 6; do
    curl -fsS --retry 3 --retry-all-errors --connect-timeout 20 -o "$out.part" "https://www.jlpt.jp/samples/$p" && mv "$out.part" "$out" && ok && { echo "ok   $out"; return; }
    sleep 3
  done
  echo "FAIL $out"
}
[ -n "$1" ] && { fetch "$1"; exit; }
xargs -P 4 -I{} sh scratch/download.sh {} < scratch/links.txt
