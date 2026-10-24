"""Markdown kaynaklarını değiştirmeden yerel Quarto kitabı üretir."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import threading
from datetime import datetime, timedelta, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LESSONS = HERE.parent
BUILD = HERE / '.build'
OUTPUT = ROOT / 'output' / 'rehber'
OMIT = {'Sorularımız ve netleşen noktalar', 'Kaynaklar ve doğrulama', 'Devam notu'}


def quarto_path() -> str:
    found = shutil.which('quarto')
    if found:
        return found
    candidates = list((ROOT / '.tools').glob('quarto*/**/bin/quarto.exe'))
    candidates += list((ROOT / '.tools').glob('quarto*/**/bin/quarto.cmd'))
    for parent in [Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Quarto', Path('C:/Program Files/Quarto')]:
        candidates += [parent / 'bin' / 'quarto.exe', parent / 'bin' / 'quarto.cmd']
    for item in candidates:
        if item.is_file():
            return str(item)
    raise SystemExit('Quarto bulunamadi. Resmi Windows kurulumunu yapin: https://quarto.org/docs/download/')


def save(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding='utf-8') != text:
        path.write_text(text, encoding='utf-8')


def prepare() -> None:
    settings = json.loads((HERE / 'kitap.json').read_text(encoding='utf-8-sig'))
    BUILD.mkdir(exist_ok=True)
    included = {}
    for number, relative in enumerate(settings['chapters'], 1):
        source = (LESSONS / relative).resolve()
        if not source.is_relative_to(LESSONS.resolve()):
            raise ValueError('Konu yolu dersler disina cikamaz')
        included[source] = f'bolum-{number:02}.qmd'
    generated = []
    for source, name in included.items():
        text = source.read_text(encoding='utf-8-sig')
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
        if not match:
            raise ValueError(f'Frontmatter eksik: {source}')
        if re.search(r'^durum:\s*(bos|eski)\s*$', match[1], re.M):
            raise ValueError(f'Bos/eski konu kitaba eklenemez: {source}')
        body = text[match.end():]
        keep = True
        lines = []
        for line in body.splitlines():
            if line.startswith('## '):
                keep = line[3:].strip() not in OMIT
            if keep:
                lines.append(line)
        body = '\n'.join(lines).strip()
        def link(m):
            label, target = m.group(1), m.group(2)
            if re.match(r'^(https?://|mailto:|#)', target):
                return m.group(0)
            target_path, _, anchor = target.partition('#')
            resolved = (source.parent / target_path).resolve()
            if resolved in included:
                return f'[{label}]({included[resolved]}' + (f'#{anchor}' if anchor else '') + ')'
            # Yayımlanmayan repo içi belgeye bozuk dosya bağlantısı üretme.
            return label
        body = re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', link, body)
        blocks = re.findall(r'```mermaid\s*\n(.*?)```', body, re.S)
        if blocks:
            digest = hashlib.sha256(blocks[0].strip().encode()).hexdigest()
            known = source.name == '01-ne-yapiyoruz.md' and len(blocks) == 1 and digest == '0fc19b8feedebb04991cf04a29accf33e1950f57cdf02ce384c6e54f836fdf5f'
            if not known:
                raise ValueError(f'Yeni Mermaid icin PDF/EPUB gorseli eklenmeli: {source}')
            body = re.sub(r'```mermaid\s*\n.*?```', '![Piyasa verisinden kullanıcıya işlevsel akış](akisin-ozeti.svg){width=100%}', body, flags=re.S)
        # Göreli görüntüleri geçici kitaba taşır; kaynak dizine yazmaz.
        def picture(m):
            alt, target, attrs = m.group(1), m.group(2), m.group(3) or ''
            if target == 'akisin-ozeti.svg' or re.match(r'^https?://', target):
                return m.group(0)
            asset = (source.parent / target).resolve()
            if not asset.is_relative_to(ROOT) or not asset.is_file():
                raise ValueError(f'Gorsel bulunamadi veya repo disinda: {target}')
            dest = 'asset-' + hashlib.sha256(str(asset).encode()).hexdigest()[:12] + asset.suffix
            shutil.copyfile(asset, BUILD / dest)
            return f'![{alt}]({dest}){attrs}'
        body = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)(\{[^}]*\})?', picture, body)
        save(BUILD / name, body + '\n')
        generated.append(name)
    intro = f'''# Okumaya başlamadan {{.unnumbered}}

Bu çalışma taslağı, MeeApps uygulamasını ve sistemini temelden açıklamak için hazırlanıyor. Yalnız yazılmış ve kitap listesine eklenmiş konuları içerir; ilerledikçe yeni bölümler eklenecektir.

**Sürüm:** {settings['version']} · **Güncelleme:** {datetime.now(timezone(timedelta(hours=3))).strftime('%d.%m.%Y')} · **Kapsam:** {len(generated)} konu

PDF A4 sayfa düzeniyle hazırlanır. EPUB'da metin ekran ve yazı boyutuna göre yeniden akar; PDF ile aynı sayfa numaraları beklenmez.

Kaynak Markdown dosyaları düzenlenir; üretilen PDF, EPUB veya HTML üzerinde yapılan değişiklikler sonraki üretimde korunmaz.
'''
    save(BUILD / 'index.qmd', intro)
    config = (HERE / '_quarto.yml').read_text(encoding='utf-8')
    config = config.replace('    - index.qmd', '    - index.qmd\n' + '\n'.join('    - ' + n for n in generated))
    config = config.replace('title: "MeeApps Uygulama ve Sistem Rehberi"', 'title: ' + json.dumps(settings['title'], ensure_ascii=False))
    config = config.replace('subtitle: "Şirket içi bilgi aktarımı"', 'subtitle: ' + json.dumps(settings['subtitle'], ensure_ascii=False))
    save(BUILD / '_quarto.yml', config)
    for asset in ['styles.css', 'epub.css', 'akisin-ozeti.svg', 'typst-show.typ', 'brand-logo.png']:
        shutil.copyfile(HERE / asset, BUILD / asset)


def run(quarto: str, fmt: str) -> None:
    formats = ['typst', 'html', 'epub'] if fmt == 'all' else ['typst' if fmt == 'pdf' else fmt]
    for output_format in formats:
        subprocess.run([quarto, 'render', str(BUILD), '--to', output_format], check=True, cwd=ROOT)
        # Sonraki format Quarto'nun gecici cikti klasorunu temizleyebilir.
        OUTPUT.mkdir(parents=True, exist_ok=True)
        shutil.copytree(BUILD / '_book', OUTPUT, dirs_exist_ok=True)
        if output_format == 'typst':
            pdf = BUILD / '_book' / 'meeapps-rehber.pdf'
            pdf_output = ROOT / 'output' / 'pdf'
            pdf_output.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pdf, pdf_output / pdf.name)
    print(f'Ciktilar: {OUTPUT}')


def fingerprint():
    files = list(LESSONS.glob('[0-9][0-9]-*/**/*.md')) + list(HERE.glob('*'))
    return tuple(sorted((str(p), p.stat().st_mtime_ns) for p in files if p.is_file()))


def main():
    global BUILD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', choices=['pdf', 'html', 'epub', 'all'], default='all')
    parser.add_argument('--watch', action='store_true', help='MD kaydedilince secilen ciktilari yenile')
    parser.add_argument('--preview', action='store_true', help='Tarayicida canli HTML onizlemesi; kaynak MD degisince yenilenir')
    args = parser.parse_args()
    if args.preview:
        BUILD = HERE / '.preview'
    quarto = quarto_path()
    prepare()
    if args.preview:
        def monitor():
            previous = fingerprint()
            while True:
                time.sleep(1)
                current = fingerprint()
                if current != previous:
                    previous = current
                    try:
                        prepare()
                    except ValueError as error:
                        print(f'Kaynak hatasi: {error}')
        threading.Thread(target=monitor, daemon=True).start()
        try:
            subprocess.run([quarto, 'preview', str(BUILD), '--to', 'html', '--port', '8765', '--no-browser'], check=True, cwd=ROOT)
        except KeyboardInterrupt:
            pass
        return
    run(quarto, args.format)
    if args.watch:
        print('Kaynaklar izleniyor. Durdurmak icin Ctrl+C. Yenilenen PDF/HTML dosyasini acik tutabilirsiniz.')
        previous = fingerprint()
        try:
            while True:
                time.sleep(1)
                current = fingerprint()
                if current != previous:
                    previous = current
                    try:
                        prepare()
                        run(quarto, args.format)
                    except (ValueError, subprocess.CalledProcessError) as error:
                        print(f'Uretim hatasi; kaynak duzeltilince yeniden denenecek: {error}')
        except KeyboardInterrupt:
            print('Izleme durduruldu.')


if __name__ == '__main__':
    main()
