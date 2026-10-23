#!/usr/bin/env python3
"""Builds the animated SVGs in ../img. Seeded, so output is stable between runs."""
import math
import pathlib
import random
from html import escape

OUT = pathlib.Path(__file__).resolve().parent.parent / "img"
OUT.mkdir(exist_ok=True)

BG, FG, DIM, ACC, ERR = "#0a0b0d", "#c8ccd2", "#5b616b", "#f2b24c", "#ff5c57"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Noto Sans Mono',monospace"
NOISE = "░▒▓/\\<>+=*#%&@$0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CW, FS, LH = 9.6, 16, 24  # cell width, font size, line height
EASE = "cubic-bezier(.23,1,.32,1)"

# Base style for every SVG. Reduced motion shows the settled frame.
BASE_CSS = f"""
text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.cover,.fr{{display:none}}}}
"""


def t(x, y, s, fill=FG, cls="", style="", opacity=None):
    """One text row on the cell grid; textLength pins every glyph to its cell."""
    if not s:
        return ""
    extra = f' class="{cls}"' if cls else ""
    extra += f' style="{style}"' if style else ""
    extra += f' fill-opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" textLength="{len(s) * CW:.1f}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve"{extra}>{escape(s)}</text>')


def human_delays(s):
    out = []
    for ch in s:
        d = random.uniform(.038, .105)
        if ch == " ":
            d += random.uniform(.010, .110)
        elif ch in ".,:;!?$~/'()":
            d += random.uniform(.020, .140)
        if random.random() < .04:
            d += random.uniform(.220, .560)
        out.append(d)
    return out


def scramble_frames(s, tick=.05, lo=3, hi=9):
    """Each cell settles on its own tick, so the edge of the reveal stays ragged."""
    settle = [random.randint(lo, hi) for _ in s]
    frames = []
    for k in range(max(settle)):
        frames.append("".join(
            c if (k >= settle[i] or c == " ") else random.choice(NOISE)
            for i, c in enumerate(s)))
    return frames, max(settle) * tick


# ---------------------------------------------------------------- boot.svg

def build_boot():
    random.seed(7)
    W, PAD = 880, 28
    css, body = [BASE_CSS], []
    script = [
        ("type", "$ ", "nvim ~/."),
        ("out", DIM, '"[No Name]" 0L, 0B'),
        ("type", "", ":whoami"),
        ("out", ERR, "E492: Not an editor command: whoami"),
        ("type", "", ":echo $USER"),
        ("out", ERR, "E121: Undefined variable: $USER"),
        ("type", "", ":pwd"),
        ("out", DIM, "/void"),
        ("type", "", ":set noname nofile nohistory"),
        ("out", ACC, "-- the wall is listening --"),
    ]
    now = .9
    y = PAD + 44
    body.append(t(PAD, PAD + 8, "~/.  ─  nvim  ─  [No Name]", DIM, opacity=.7))
    body.append(f'<rect x="{PAD}" y="{PAD + 18}" width="{W - 2 * PAD}" height="1" fill="{DIM}" fill-opacity=".35"/>')
    for i, (kind, a, b) in enumerate(script):
        if kind == "type":
            prompt, cmd = a, b
            x0 = PAD + len(prompt) * CW
            body.append(t(PAD, y, prompt, DIM))
            body.append(t(x0, y, cmd, FG))
            delays = human_delays(cmd)
            total = sum(delays)
            stops, acc = [], 0
            for n, d in enumerate(delays):
                acc += d
                stops.append(f"{acc / total * 100:.2f}%{{transform:translateX({(n + 1) * CW:.1f}px)}}")
            css.append(f"@keyframes ty{i}{{0%{{transform:translateX(0)}}{''.join(stops)}}}")
            css.append(f".cv{i}{{animation:ty{i} {total:.2f}s step-end {now:.2f}s both}}")
            css.append(f".ca{i}{{opacity:0;animation:on {total + .35:.2f}s step-end {now - .5:.2f}s}}")
            # The cover hides untyped text; the caret rides on its left edge.
            body.append(
                f'<g class="cover cv{i}"><rect x="{x0:.1f}" y="{y - 17}" width="{len(cmd) * CW + CW:.1f}" '
                f'height="{LH}" fill="{BG}"/><rect class="ca{i}" x="{x0:.1f}" y="{y - 16}" width="{CW:.1f}" '
                f'height="20" fill="{ACC}"/></g>')
            now += total + random.uniform(.25, .45)
        else:
            color, msg = a, b
            frames, dur = scramble_frames(msg)
            for k, f in enumerate(frames):
                body.append(t(PAD, y, f, color, cls="fr", style=f"animation-delay:{now + k * .05:.2f}s", opacity=.8))
            body.append(t(PAD, y, msg, color, style=f"animation:show .01s linear {now + dur:.2f}s both"))
            now += dur + random.uniform(.6, 1.1)
        y += LH
    # Final idle caret: blinks at 530 ms forever.
    body.append(f'<rect x="{PAD}" y="{y - 16}" width="{CW:.1f}" height="20" fill="{ACC}" '
                f'style="animation:show .01s linear {now:.2f}s both,blink 1.06s step-end {now:.2f}s infinite"/>')
    H = y + PAD
    glitch_start = now + 1.5
    css.append(f"""
@keyframes on{{from,to{{opacity:1}}}}
@keyframes show{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}}}
.fr{{opacity:0;animation:on .06s linear}}
@keyframes jit{{0%,88.9%,92.1%,100%{{transform:none}}89%{{transform:translate(3px,0) skewX(-6deg)}}89.8%{{transform:translate(-4px,0)}}90.6%{{transform:translate(1px,0) skewX(3deg)}}91.4%{{transform:translate(-1px,0)}}}}
@keyframes gr{{0%,88.9%,92.1%,100%{{opacity:0;transform:none}}89%{{opacity:.9;transform:translate(-5px,0)}}90%{{transform:translate(4px,0)}}91%{{opacity:.7;transform:translate(-2px,0)}}}}
@keyframes gc{{0%,89.4%,92.4%,100%{{opacity:0;transform:none}}89.5%{{opacity:.9;transform:translate(6px,0)}}90.6%{{transform:translate(-3px,0)}}91.8%{{opacity:.6;transform:translate(2px,0)}}}}
.jit{{animation:jit 6.7s linear {glitch_start:.2f}s infinite}}
.gr{{opacity:0;mix-blend-mode:screen;animation:gr 6.7s linear {glitch_start:.2f}s infinite}}
.gc{{opacity:0;mix-blend-mode:screen;animation:gc 6.7s linear {glitch_start:.2f}s infinite}}
""")
    bands = lambda seed: "".join(
        f'<rect x="0" y="{random.Random(seed + k).randint(0, H)}" width="{W}" height="{random.Random(seed * 9 + k).randint(6, 40)}"/>'
        for k in range(4))
    content = "".join(body)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>{''.join(css)}</style>
<defs>
<filter id="red"><feColorMatrix values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0"/></filter>
<filter id="cyan"><feColorMatrix values="0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1 0"/></filter>
<clipPath id="b1">{bands(3)}</clipPath><clipPath id="b2">{bands(11)}</clipPath>
</defs>
<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>
<g class="jit">{content}</g>
<g clip-path="url(#b1)"><g class="gr" filter="url(#red)">{content}</g></g>
<g clip-path="url(#b2)"><g class="gc" filter="url(#cyan)">{content}</g></g>
</svg>
"""
    (OUT / "boot.svg").write_text(svg)


# ---------------------------------------------------------------- eye.svg

def build_eye():
    random.seed(13)
    W, LHE = 880, 18
    cols, rows = int(W // CW), 22
    H = rows * LHE + 12
    cx, cy = W / 2, H / 2
    A, B = 300, 132  # almond half-width / half-height in px

    # The wall behind the eye is made of this very README, read back as glyphs.
    src = ("<!-- 79 6f 75 --> <details><summary>door 0x03</summary> dGhlIHN0YXR1c2xpbmUg "
           "E492: Not an editor command E486: Pattern not found: me :set noname ~ ~ ~ "
           "the wall is not noise. it only looks like it. gur ynfg xrl ")
    wall = []
    for r in range(rows):
        off = random.randint(0, len(src))
        line = (src * 3)[off:off + cols]
        wall.append(t(0, 14 + r * LHE, line, DIM, opacity=round(random.uniform(.10, .2), 2)))

    def inside(x, y, a=A, b=B):
        dx = (x - cx) / a
        return abs(dx) < 1 and abs(y - cy) < b * (1 - dx * dx)

    # Sclera: shade by distance to the lid edge, quantised to a few glyph levels.
    shades = " .·:-=+"
    rowsS = []
    for r in range(rows):
        y = 14 + r * LHE - 5
        line = ""
        for c in range(cols):
            x = c * CW + CW / 2
            if not inside(x, y):
                line += " "
                continue
            dx = (x - cx) / A
            edge = B * (1 - dx * dx)
            depth = 1 - abs(y - cy) / max(edge, 1)
            line += shades[min(len(shades) - 1, int(depth * len(shades)))]
        rowsS.append(t(0, 14 + r * LHE, line, FG, opacity=.35))

    # Iris and pupil live on their own grid so they move as one rigid object.
    IR, PR = 86, 34
    iris, pupil = [], []
    for r in range(-6, 7):
        y = r * LHE
        li, lp = "", ""
        for c in range(-11, 12):
            x = c * CW
            d = math.hypot(x, y * 1.0)
            ang = math.atan2(y, x)
            if d < PR:
                li += " "
                lp += "@"
            elif d < IR:
                fiber = (math.sin(ang * 9) + math.sin(ang * 23 + d * .08)) * .5
                ring = (d - PR) / (IR - PR)
                li += "%#*+=-"[min(5, int((ring * .7 + (fiber + 1) * .15) * 6))]
                lp += " "
            else:
                li += " "
                lp += " "
        x0 = -11 * CW
        iris.append(t(x0, y + 5, li, ACC, opacity=.9))
        pupil.append(t(x0, y + 5, lp, FG, opacity=.95))
    glint = t(-2 * CW, -LHE + 5, "°", "#ffffff")

    almond = f"M{cx - A},{cy} Q{cx},{cy - 2 * B} {cx + A},{cy} Q{cx},{cy + 2 * B} {cx - A},{cy}Z"
    lid_rows = lambda n: "".join(
        t(cx - A, cy - B - 4 - k * LHE, "▓" * int(2 * A / CW), DIM, opacity=.55) for k in range(n))
    lid_rows_low = lambda n: "".join(
        t(cx - A, cy + B + 14 + k * LHE, "▓" * int(2 * A / CW), DIM, opacity=.55) for k in range(n))

    blink = "0%,21.9%,23.5%,59.9%,61.3%,62.1%,63.5%,100%{transform:none}22.7%,60.6%,62.8%"
    css = BASE_CSS + f"""
@keyframes up{{{blink}{{transform:translateY({B + 2}px)}}}}
@keyframes dn{{{blink}{{transform:translateY(-{B + 2}px)}}}}
@keyframes gaze{{
0%,9%{{transform:translate({cx}px,{cy}px)}}
11%,27%{{transform:translate({cx - 150}px,{cy - 22}px)}}
29%,38%{{transform:translate({cx + 120}px,{cy - 30}px)}}
40%,66%{{transform:translate({cx + 8}px,{cy + 52}px)}}
68%,80%{{transform:translate({cx + 170}px,{cy + 12}px)}}
82%,100%{{transform:translate({cx}px,{cy}px)}}}}
@keyframes dil{{0%,100%{{transform:scale(1)}}35%{{transform:scale(.72)}}70%{{transform:scale(1.18)}}}}
.ul{{animation:up 11.7s ease-in-out infinite}}
.ll{{animation:dn 11.7s ease-in-out infinite}}
.iris{{transform:translate({cx}px,{cy}px);animation:gaze 14.3s {EASE} infinite}}
.pup{{transform-box:view-box;transform-origin:0 0;animation:dil 9.1s ease-in-out infinite}}
"""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>{css}</style>
<defs><clipPath id="eye"><path d="{almond}"/></clipPath></defs>
<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>
{''.join(wall)}
<path d="{almond}" fill="{BG}"/>
<g clip-path="url(#eye)">
{''.join(rowsS)}
<g class="iris">{''.join(iris)}<g class="pup">{''.join(pupil)}</g>{glint}</g>
<g class="ul"><rect x="{cx - A}" y="{cy - 2 * B - 4}" width="{2 * A}" height="{B + 4}" fill="{BG}"/>{lid_rows(8)}</g>
<g class="ll"><rect x="{cx - A}" y="{cy + B}" width="{2 * A}" height="{B + 4}" fill="{BG}"/>{lid_rows_low(8)}</g>
</g>
<path d="{almond}" fill="none" stroke="{FG}" stroke-opacity=".25"/>
</svg>
"""
    (OUT / "eye.svg").write_text(svg)


# ---------------------------------------------------------------- statusline.svg

def build_statusline():
    random.seed(21)
    W, H = 880, 30
    y = 20
    mode = " NORMAL "
    mw = len(mode) * CW
    name = " [No Name] "
    rot = "gur ynfg xrl fyrrcf va gur fbhepr"
    right = "utf-8 │ 0x00 │ 0:0 │ Top "
    rx = W - len(right) * CW

    # Every 9 s the mode label scrambles for three 50 ms frames, then settles.
    frames, _ = scramble_frames(mode, lo=1, hi=3)
    frame_svg = "".join(
        t(0, y, f, BG, cls="mf", style=f"animation-delay:{4 + k * .05:.2f}s") for k, f in enumerate(frames))
    css = BASE_CSS + f"""
@keyframes blip{{0%,.55%{{opacity:1}}.56%,100%{{opacity:0}}}}
@keyframes hide{{0%,{len(frames) * .56:.2f}%{{opacity:0}}{len(frames) * .56 + .01:.2f}%,100%{{opacity:1}}}}
.mf{{opacity:0;animation:blip 9s step-end infinite}}
.mode{{animation:hide 9s step-end 4s infinite}}
@media (prefers-reduced-motion:reduce){{.mf{{display:none}}}}
"""
    # vim's empty-buffer tildes sit above the bar, as in a real window.
    tildes = "".join(t(0, 16 + k * 22, "~", "#3d4a66") for k in range(3))
    top = 3 * 22
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H + top}" width="{W}" height="{H + top}">
<style>{css}</style>
{tildes}
<g transform="translate(0 {top})">
<rect width="{W}" height="{H}" rx="6" fill="#16181c"/>
<rect width="{mw:.1f}" height="{H}" rx="6" fill="{ACC}"/>
{t(0, y, mode, BG, cls="mode")}
{frame_svg}
<rect x="{mw:.1f}" width="{len(name) * CW:.1f}" height="{H}" fill="#23262c"/>
{t(mw, y, name, FG)}
{t(mw + len(name) * CW + 2 * CW, y, rot, DIM)}
{t(rx, y, right, DIM)}
</g>
</svg>
"""
    (OUT / "statusline.svg").write_text(svg)


# ---------------------------------------------------------------- wall.svg

def build_wall():
    """Noise that never sits still, and sixteen letters that never move. Stillness is the signal."""
    random.seed(5)
    W, PAD, LHW = 880, 24, 22
    cols, rows = int((W - 2 * PAD) // CW), 14
    H = rows * LHW + 2 * PAD
    GRAY = "#7d8590"
    noise = "░▒▓/\\<>+=*#%&@$·:;0123456789╱╲┼"
    msg = "OPENTHETHIRDDOOR"
    cells = sorted(random.sample(range(cols, cols * (rows - 1)), len(msg)))
    hidden = {divmod(c, cols): ch for c, ch in zip(cells, msg)}
    F = 6  # flipbook frames per row

    def row_text(y, s, cls="", style="", fill=None):
        attrs = f' class="{cls}"' if cls else ""
        attrs += f' style="{style}"' if style else ""
        attrs += f' fill="{fill}"' if fill else ""
        return (f'<text x="{PAD}" y="{y}" textLength="{len(s) * CW:.1f}" lengthAdjust="spacingAndGlyphs" '
                f'xml:space="preserve"{attrs}>{escape(s)}</text>')

    css = [BASE_CSS, f"""
@keyframes fb{{0%,{100 / F + .4:.2f}%{{opacity:1}}{100 / F + .5:.2f}%,100%{{opacity:0}}}}
.f{{opacity:0}}.f0{{opacity:1}}
@keyframes wave{{0%,78%,100%{{fill:{GRAY}}}82%{{fill:{ACC}}}86%{{fill:{ERR}}}90%{{fill:#5ce1e6}}94%{{fill:{GRAY}}}}}
@keyframes j0{{0%,47%,49.4%,100%{{transform:none}}47.2%{{transform:translateX(14px)}}48%{{transform:translateX(-9px)}}48.8%{{transform:translateX(4px)}}}}
@keyframes j1{{0%,71%,73.2%,100%{{transform:none}}71.3%{{transform:translateX(-22px)}}72.4%{{transform:translateX(6px)}}}}
@keyframes j2{{0%,12%,14%,100%{{transform:none}}12.2%{{transform:translateX(31px) skewX(-20deg)}}13.1%{{transform:translateX(-12px)}}}}
@keyframes scan{{0%{{transform:translateY(-70px);opacity:.22}}100%{{transform:translateY({H + 10}px);opacity:.22}}}}
@keyframes glow{{0%{{opacity:.95}}14%,100%{{opacity:0}}}}
@keyframes quake{{0%,89.9%,92.4%,100%{{transform:none}}90.2%{{transform:translate(-6px,2px) skewX(8deg)}}90.9%{{transform:translate(9px,-1px) skewX(-14deg) scaleY(1.05)}}91.6%{{transform:translate(-3px,0)}}}}
@keyframes rgbR{{0%,89.9%,92.4%,100%{{opacity:0;transform:none}}90%{{opacity:.95;transform:translate(-9px,1px)}}91.2%{{opacity:.8;transform:translate(5px,0)}}}}
@keyframes rgbC{{0%,90.3%,92.6%,100%{{opacity:0;transform:none}}90.4%{{opacity:.95;transform:translate(10px,-1px)}}91.6%{{opacity:.7;transform:translate(-4px,0)}}}}
@keyframes tear{{0%,90.1%,90.6%,91.1%,91.9%,100%{{opacity:0}}90.2%,90.5%,91.2%,91.8%{{opacity:1}}}}
@keyframes smear{{0%,90.5%,91.5%,100%{{transform:none}}90.6%,91.4%{{transform:scaleX(2.6)}}}}
@keyframes visit{{0%,4.4%,100%{{opacity:0}}0.4%,4%{{opacity:1}}}}
.scan{{opacity:0;mix-blend-mode:screen;animation:scan 4.2s linear infinite}}
.gl,.rgb,.tear,.visit{{opacity:0}}
.all{{animation:quake 8.3s linear 2s infinite}}
.rgbR{{mix-blend-mode:screen;animation:rgbR 8.3s linear 2s infinite}}
.rgbC{{mix-blend-mode:screen;animation:rgbC 8.3s linear 2s infinite}}
.tear{{mix-blend-mode:difference;animation:tear 8.3s linear 2s infinite}}
.smear{{transform-box:fill-box;transform-origin:left;animation:smear 8.3s linear 2s infinite}}
"""]
    body, static = [], []
    smear_rows = set(random.sample(range(rows), 2))
    for r in range(rows):
        y = PAD + 16 + r * LHW
        base = [" " if (r, c) in hidden or random.random() < .12 else random.choice(noise) for c in range(cols)]
        frames = [base]
        for _ in range(F - 1):
            frames.append([c if c == " " or random.random() > .5 else random.choice(noise) for c in frames[-1]])
        tick = random.choice([.1, .15, .2])
        period = F * tick
        off = round(random.uniform(0, period), 2)  # keeps frame delays exact, so rows never blank out
        flips = "".join(
            row_text(y, "".join(f), cls=f"f f{k}", style=f"animation:fb {period:.2f}s linear {k * tick - period - off:.2f}s infinite")
            for k, f in enumerate(frames))
        letters = "".join(hidden.get((r, c), " ") for c in range(cols))
        has_letters = letters.strip() != ""
        # A white copy of the letters flares as the scanline crosses their row.
        reach = (y + 70) / (H + 80) * 4.2
        glow = row_text(y, letters, cls="gl", fill="#ffffff", style=f"animation:glow 4.2s linear {reach:.2f}s infinite") if has_letters else ""
        lit = row_text(y, letters) if has_letters else ""
        jit = f"j{random.randint(0, 2)} {random.choice([3.1, 4.7, 5.9, 7.3, 9.7])}s linear {-random.uniform(0, 9):.2f}s infinite"
        inner = f'<g class="smear">{flips}{lit}{glow}</g>' if r in smear_rows else flips + lit + glow
        body.append(f'<g fill="{GRAY}" style="animation:{jit},wave 6s linear {r * .07:.2f}s infinite">{inner}</g>')
        static.append(row_text(y, "".join(base)) + lit)

    # The eye visits the wall now and then, and leaves before anyone is sure.
    visits = []
    for k in range(3):
        c, r = random.randint(4, cols - 8), random.randint(1, rows - 2)
        x, y = PAD + c * CW, PAD + 16 + r * LHW
        visits.append(
            f'<g class="visit" style="animation:visit 13s linear {2.5 + k * 4.1:.1f}s infinite">'
            f'<rect x="{x - 2:.1f}" y="{y - 17}" width="{3 * CW + 4:.1f}" height="{LHW}" fill="{BG}"/>'
            f'{t(x, y, "(◉)", ACC)}</g>')
    tears = "".join(
        f'<rect class="tear" x="0" y="{random.randint(PAD, H - PAD)}" width="{W}" height="{random.randint(4, 26)}" fill="#ffffff"/>'
        for _ in range(3))
    frame0 = "".join(static)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>{''.join(css)}</style>
<defs>
<filter id="red"><feColorMatrix values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0"/></filter>
<filter id="cyan"><feColorMatrix values="0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1 0"/></filter>
<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ACC}" stop-opacity="0"/><stop offset=".7" stop-color="{ACC}"/><stop offset="1" stop-color="#ffffff"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>
<g class="all">{''.join(body)}{''.join(visits)}</g>
<g class="rgb rgbR" fill="{GRAY}" filter="url(#red)">{frame0}</g>
<g class="rgb rgbC" fill="{GRAY}" filter="url(#cyan)">{frame0}</g>
<rect class="scan" x="0" y="0" width="{W}" height="60" fill="url(#sg)"/>
{tears}
</svg>
"""
    (OUT / "wall.svg").write_text(svg)


if __name__ == "__main__":
    build_wall()
    build_boot()
    build_eye()
    build_statusline()
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.svg"))))
