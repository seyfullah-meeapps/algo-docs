// Quarto'nun kitap filtresi korunur; ekran okumaya uygun tek yüzlü tasarım.
#set text(font: "$mainfont$", size: $fontsize$, lang: "tr", fill: rgb("#20354a"))
#set par(justify: false, first-line-indent: 0pt, leading: 0.65em, spacing: 0.75em)
#set heading(numbering: "1.1")
#set table(inset: 7pt, stroke: 0.4pt + rgb("#ced8e0"))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table.cell.where(y: 0): set table.cell(fill: rgb("#edf2f7"))
#show link: set text(fill: rgb("#246b88"))
#set page(footer: context align(center, text(size: 9pt, fill: rgb("#63768a"), counter(page).display("1"))))

#align(center)[
  #v(38mm)
  #text(size: 12pt, tracking: 2pt, fill: rgb("#63768a"))[MEEAPPS]
  #v(9mm)
  #text(size: 28pt, weight: "bold")[$title$]
  #v(7mm)
  #text(size: 13pt)[$subtitle$]
  #v(14mm)
  #line(length: 38mm, stroke: 2pt + rgb("#246b88"))
  #v(8mm)
  #text(size: 10pt)[A4 okuma sürümü · Çalışma taslağı]
]
#pagebreak()
#outline(title: [İçindekiler], depth: $toc-depth$)
#pagebreak()

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block(above: 0pt, below: 8mm)[#text(size: 20pt, weight: "bold")[#it]]
}
#show heading.where(level: 2): it => block(above: 5mm, below: 3mm)[#text(size: 14pt, weight: "bold")[#it]]
