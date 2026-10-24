// Frontend light/dark tokenları: brand #94c04e, ink #333, strong #212121.
#let brand = rgb("#94c04e")
#let ink = rgb("#333333")
#let heading-ink = rgb("#212121")
#let muted = rgb("#6b6b6b")
#let border = rgb("#d9d9d9")
#set text(font: "$mainfont$", size: $fontsize$, lang: "tr", fill: ink)
#set par(justify: false, first-line-indent: 0pt, leading: 0.68em, spacing: 0.95em)
#set heading(numbering: "1.1")
#set list(spacing: 0.5em)
#set enum(spacing: 0.5em)
#set table(inset: 8pt, stroke: 0.4pt + border)
#show table: set text(size: 9pt)
#show table.cell.where(y: 0): set text(weight: "bold", fill: heading-ink)
#show table.cell.where(y: 0): set table.cell(fill: rgb("#f4f4f5"))
#show link: set text(fill: rgb("#15803d"))
#set page(
  header: context {
    if counter(page).get().first() > 1 {
      text(size: 8pt, fill: muted)[MeeApps / Uygulama ve Sistem Rehberi]
      v(2mm)
      line(length: 100%, stroke: 0.5pt + border)
    }
  },
  footer: context {
    line(length: 100%, stroke: 0.5pt + border)
    v(2mm)
    grid(columns: (1fr, auto),
      text(size: 8pt, fill: muted)[Şirket içi bilgi aktarımı],
      text(size: 8pt, fill: muted)[#counter(page).display("1")],
    )
  },
)

#page(fill: white, header: none, footer: none, numbering: none)[
  #set text(fill: black)
  #v(8mm)
  #block(fill: brand, inset: 7mm, radius: 3mm)[#image("brand-logo.png", width: 40mm)]
  #v(33mm)
  #line(length: 24mm, stroke: 3pt + brand)
  #v(10mm)
  #text(size: 29pt, weight: "bold", fill: black, tracking: -0.2pt)[$title$]
  #v(9mm)
  #text(size: 12pt, fill: black)[$subtitle$]
  #v(1fr)
  #line(length: 100%, stroke: 0.5pt + border)
  #v(5mm)
  #grid(columns: (1fr, auto),
    text(size: 9pt, fill: black)[BIST · Algo / HFT],
    text(size: 9pt, fill: black)[A4 okuma sürümü],
  )
]

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block(above: 0pt, below: 9mm, sticky: true)[
    #line(length: 12mm, stroke: 2pt + brand)
    #v(4mm)
    #text(size: 18pt, weight: "bold", fill: heading-ink)[#it]
  ]
}
#show heading.where(level: 2): set text(size: 12pt, weight: "bold", fill: heading-ink)
#show heading.where(level: 2): set block(above: 7mm, below: 3.5mm)
#show heading.where(level: 3): set text(size: 10.5pt, weight: "bold", fill: heading-ink)
#show heading.where(level: 3): set block(above: 5mm, below: 2.5mm)
#outline(title: [İçindekiler], depth: $toc-depth$)
#pagebreak()
