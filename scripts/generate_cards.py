#!/usr/bin/env python3
"""
Generates animated, theme-consistent GitHub stats cards (SVG) for a profile README.

Uses only the Python standard library and a single GitHub GraphQL request.
Output: stats/overview.svg, stats/streak.svg, stats/activity.svg, stats/languages.svg

Env:
  GH_TOKEN / GITHUB_TOKEN  token for the GraphQL API
  USERNAME                 GitHub username (defaults to the repo owner)
  OUT_DIR                  output folder (default: stats)
  DEMO=1                   render with fake data (no network) for a local preview
"""
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Junaed10"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT_DIR", "stats")
W = 700

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    allRepos: repositories(ownerAffiliations: OWNER) { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# ----------------------------------------------------------------------------- data
def fetch():
    if not TOKEN:
        sys.exit("Missing GH_TOKEN / GITHUB_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-cards",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.load(r)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        sys.exit(f"GraphQL error: {payload.get('errors')}")
    u = payload["data"]["user"]
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]
    weeks = [
        [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for d in w["contributionDays"]]
        for w in cal["weeks"]
        if w["contributionDays"]
    ]
    langs = {}
    stars = 0
    for repo in u["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {
        "login": u["login"],
        "followers": u["followers"]["totalCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "repos": u["allRepos"]["totalCount"],
        "stars": stars,
        "commits": cc["totalCommitContributions"],
        "contrib": cal["totalContributions"],
        "weeks": weeks,
        "langs": sorted(langs.items(), key=lambda x: -x[1]),
    }


def demo():
    rnd = random.Random(7)
    start = dt.date.today() - dt.timedelta(days=7 * 52 + dt.date.today().weekday() + 1)
    weeks, day = [], start
    for _ in range(53):
        w = []
        for _ in range(7):
            if day <= dt.date.today():
                busy = rnd.random() < 0.55
                w.append((day, rnd.randint(1, 9) if busy else 0))
            day += dt.timedelta(days=1)
        weeks.append(w)
    total = sum(c for w in weeks for _, c in w)
    return {
        "login": USER, "followers": 128, "prs": 342, "issues": 87, "repos": 41, "stars": 1260,
        "commits": int(total * 0.8), "contrib": total, "weeks": weeks,
        "langs": [("TypeScript", 520000), ("Python", 410000), ("JavaScript", 260000),
                  ("CSS", 90000), ("Java", 70000), ("PHP", 40000), ("HTML", 30000)],
    }


# ----------------------------------------------------------------------------- svg kit
CSS = """
text{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,Ubuntu,'Helvetica Neue',Arial,sans-serif}
.t{fill:#e2e8f0;font-size:17px;font-weight:600}
.m{fill:#94a3b8;font-size:12px}
.u{fill:#94a3b8;font-size:11px;font-weight:600;letter-spacing:.08em}
.s{fill:#64748b;font-size:11px}
.v{fill:#f8fafc;font-size:28px;font-weight:700}
.l{fill:#cbd5e1;font-size:13px;font-weight:600}
.fade{animation:fade .7s cubic-bezier(.22,1,.36,1) both}
@keyframes fade{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.grow{transform-box:fill-box;transform-origin:left center;animation:grow 1.3s cubic-bezier(.22,1,.36,1) both}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.draw{animation:draw 2.4s cubic-bezier(.4,0,.2,1) both}
.appear{animation:appear 1.2s ease-out both}
@keyframes appear{from{opacity:0}to{opacity:1}}
.pop{transform-box:fill-box;transform-origin:center;animation:pop .6s cubic-bezier(.34,1.56,.64,1) both}
@keyframes pop{from{opacity:0;transform:scale(0)}to{opacity:1;transform:scale(1)}}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.6s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.55;transform:scale(1)}50%{opacity:0;transform:scale(2.2)}}
.glow{animation:glow 3s ease-in-out infinite}
@keyframes glow{0%,100%{opacity:1}50%{opacity:.6}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""

DEFS = """
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#101a30"/></linearGradient>
<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset=".55" stop-color="#6366f1"/><stop offset="1" stop-color="#a78bfa"/></linearGradient>
<linearGradient id="accentV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#6366f1"/></linearGradient>
<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22d3ee" stop-opacity=".38"/><stop offset=".6" stop-color="#6366f1" stop-opacity=".12"/><stop offset="1" stop-color="#6366f1" stop-opacity="0"/></linearGradient>
"""

PALETTE = [("#22d3ee", "#38bdf8"), ("#38bdf8", "#6366f1"), ("#6366f1", "#8b5cf6"),
           ("#8b5cf6", "#a78bfa"), ("#2dd4bf", "#22d3ee"), ("#a78bfa", "#e879f9")]
FLAME = ('<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 '
         '2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>')


def wrap(w, h, title, body, extra_css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<defs>{DEFS}<style>{CSS}{extra_css}</style></defs>\n"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="url(#bg)" stroke="#1e293b"/>\n'
        f"{body}\n</svg>\n"
    )


def header(title, right=""):
    r = f'<text x="{W - 35}" y="38" text-anchor="end" class="m">{escape(right)}</text>' if right else ""
    return (
        f'<g class="fade"><text x="35" y="38" class="t">{escape(title)}</text>{r}</g>'
        f'<rect class="grow" x="35" y="48" width="56" height="3" rx="1.5" fill="url(#accent)"/>'
    )


def n(v):
    return f"{v:,}"


def fdate(d):
    return d.strftime("%b %d").replace(" 0", " ")


# ----------------------------------------------------------------------------- cards
def card_overview(d):
    tiles = [
        ("CONTRIBUTIONS", d["contrib"], "last 12 months"),
        ("COMMITS", d["commits"], "last 12 months"),
        ("PULL REQUESTS", d["prs"], "all time"),
        ("ISSUES", d["issues"], "all time"),
        ("STARS EARNED", d["stars"], "across repositories"),
        ("FOLLOWERS", d["followers"], "on GitHub"),
    ]
    tw, th, gx, gy, x0, y0 = 200, 82, 15, 14, 35, 70
    body = header("GitHub Overview", f"@{d['login']}  ·  {d['repos']} repositories")
    for i, (label, val, sub) in enumerate(tiles):
        c1, c2 = PALETTE[i % len(PALETTE)]
        x, y = x0 + (i % 3) * (tw + gx), y0 + (i // 3) * (th + gy)
        body += (
            f'<g transform="translate({x} {y})"><g class="fade" style="animation-delay:{0.15 + i * 0.09:.2f}s">'
            f'<rect width="{tw}" height="{th}" rx="11" fill="#0e1a2f" stroke="#1e293b"/>'
            f'<rect x="0" y="16" width="3.5" height="{th - 32}" rx="1.75" fill="{c1}"/>'
            f'<text x="20" y="27" class="u">{label}</text>'
            f'<text x="20" y="57" class="v">{n(val)}</text>'
            f'<text x="20" y="73" class="s">{sub}</text></g></g>'
        )
    h = y0 + 2 * th + gy + 30
    return wrap(W, h, "GitHub overview", body)


def streaks(weeks):
    days = [x for w in weeks for x in w]
    days.sort(key=lambda x: x[0])
    # current streak (today may still be empty)
    i = len(days) - 1
    if i >= 0 and days[i][1] == 0:
        i -= 1
    end = i
    while i >= 0 and days[i][1] > 0:
        i -= 1
    cur = end - i
    cur_rng = (days[i + 1][0], days[end][0]) if cur else None
    # longest streak
    best, best_rng, run, s = 0, None, 0, 0
    for k, (_, c) in enumerate(days):
        if c > 0:
            if run == 0:
                s = k
            run += 1
            if run > best:
                best, best_rng = run, (days[s][0], days[k][0])
        else:
            run = 0
    return cur, cur_rng, best, best_rng, (days[0][0], days[-1][0])


def rng(r):
    return "—" if not r else (fdate(r[0]) if r[0] == r[1] else f"{fdate(r[0])} – {fdate(r[1])}")


def card_streak(d):
    cur, cur_r, best, best_r, span = streaks(d["weeks"])
    h = 192
    pct = 0 if best == 0 else min(100, round(100 * cur / best, 1))
    circ = 2 * math.pi * 44
    arc = circ * pct / 100
    css = f"@keyframes ring{{from{{stroke-dasharray:0 {circ:.1f}}}to{{stroke-dasharray:{arc:.1f} {circ:.1f}}}}}"
    cols = (117, 350, 583)
    body = (
        f'<line x1="233.5" y1="34" x2="233.5" y2="{h - 34}" stroke="#1e293b"/>'
        f'<line x1="466.5" y1="34" x2="466.5" y2="{h - 34}" stroke="#1e293b"/>'
        # total
        f'<g class="fade"><text x="{cols[0]}" y="98" text-anchor="middle" font-size="36" font-weight="700" fill="url(#accent)" '
        f'>{n(d["contrib"])}</text>'
        f'<text x="{cols[0]}" y="140" text-anchor="middle" class="l">Total contributions</text>'
        f'<text x="{cols[0]}" y="160" text-anchor="middle" class="s">{fdate(span[0])} – {fdate(span[1])}</text></g>'
        # current ring
        f'<g class="fade" style="animation-delay:.15s">'
        f'<circle cx="{cols[1]}" cy="76" r="44" fill="none" stroke="#1e293b" stroke-width="7"/>'
        f'<circle class="glow" cx="{cols[1]}" cy="76" r="44" fill="none" stroke="url(#accentV)" stroke-width="7" stroke-linecap="round" '
        f'stroke-dasharray="{arc:.1f} {circ:.1f}" transform="rotate(-90 {cols[1]} 76)" style="animation:ring 1.8s cubic-bezier(.4,0,.2,1) .4s both,glow 3s ease-in-out 2.2s infinite"/>'
        f'<g transform="translate({cols[1] - 9.6} 40) scale(.8)" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{FLAME}</g>'
        f'<text x="{cols[1]}" y="90" text-anchor="middle" font-size="30" font-weight="700" fill="#f8fafc">{n(cur)}</text>'
        f'<text x="{cols[1]}" y="140" text-anchor="middle" class="l">Current streak</text>'
        f'<text x="{cols[1]}" y="160" text-anchor="middle" class="s">{escape(rng(cur_r))}</text></g>'
        # longest
        f'<g class="fade" style="animation-delay:.3s"><text x="{cols[2]}" y="98" text-anchor="middle" font-size="36" font-weight="700" fill="url(#accent)" '
        f'>{n(best)}</text>'
        f'<text x="{cols[2]}" y="140" text-anchor="middle" class="l">Longest streak</text>'
        f'<text x="{cols[2]}" y="160" text-anchor="middle" class="s">{escape(rng(best_r))}</text></g>'
    )
    return wrap(W, h, "Contribution streak", body, css)


def card_activity(d):
    weeks = d["weeks"]
    ws = [sum(c for _, c in w) for w in weeks]
    n_w = len(ws)
    h = 290
    cx0, cx1, cy0, cy1 = 62, 665, 82, 224
    ymax = max(4, math.ceil(max(ws) / 4) * 4)
    X = lambda i: cx0 + i * (cx1 - cx0) / max(1, n_w - 1)
    Y = lambda v: cy1 - (v / ymax) * (cy1 - cy0)
    pts = [(X(i), Y(v)) for i, v in enumerate(ws)]
    line = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        mx = (xa + xb) / 2
        line += f" C{mx:.1f},{ya:.1f} {mx:.1f},{yb:.1f} {xb:.1f},{yb:.1f}"
    area = f"{line} L{pts[-1][0]:.1f},{cy1} L{pts[0][0]:.1f},{cy1} Z"
    # upper bound of the curve length (chord sum + margin) for the draw-on animation
    length = int(1.25 * sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))) + 20
    draw_css = (f"@keyframes draw{{from{{stroke-dasharray:{length};stroke-dashoffset:{length}}}"
                f"to{{stroke-dasharray:{length};stroke-dashoffset:0}}}}")

    body = header("Contribution Activity", "contributions per week  ·  last 12 months")
    for k in range(5):
        v = ymax * k / 4
        y = Y(v)
        body += (
            f'<line x1="{cx0}" y1="{y:.1f}" x2="{cx1}" y2="{y:.1f}" stroke="#1e293b" stroke-dasharray="3 5"/>'
            f'<text x="{cx0 - 12}" y="{y + 4:.1f}" text-anchor="end" class="s">{int(v)}</text>'
        )
    prev, last_x = None, -99
    for i, w in enumerate(weeks):
        m = w[0][0].month
        if m != prev:
            if X(i) - last_x >= 40:
                body += f'<text x="{X(i):.1f}" y="{cy1 + 24}" text-anchor="middle" class="s">{w[0][0].strftime("%b")}</text>'
                last_x = X(i)
            prev = m
    body += (
        f'<path class="appear" style="animation-delay:.8s" d="{area}" fill="url(#area)"/>'
        f'<path class="draw" d="{line}" fill="none" stroke="url(#accent)" stroke-width="2.6" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )
    peak = max(range(n_w), key=lambda i: ws[i])
    if ws[peak] > 0:
        px, py = pts[peak]
        label = f"Peak · {ws[peak]}"
        bw = 14 + 6.6 * len(label)
        bx = min(max(px - bw / 2, cx0), cx1 - bw)
        body += (
            f'<g class="appear" style="animation-delay:2.2s">'
            f'<circle class="pulse" cx="{px:.1f}" cy="{py:.1f}" r="6" fill="#22d3ee"/>'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#0b1220" stroke="#22d3ee" stroke-width="2"/>'
            f'<rect x="{bx:.1f}" y="{py - 36:.1f}" width="{bw:.1f}" height="22" rx="6" fill="#0e1a2f" stroke="#334155"/>'
            f'<text x="{bx + bw / 2:.1f}" y="{py - 21:.1f}" text-anchor="middle" font-size="11.5" font-weight="600" fill="#e2e8f0" '
            f'>{label}</text></g>'
        )
    return wrap(W, h, "Contribution activity", body, draw_css)


def card_languages(d):
    langs = d["langs"][:6]
    total = sum(s for _, s in d["langs"]) or 1
    rows = [(nm, 100 * s / total) for nm, s in langs]
    top = rows[0][1] if rows else 1
    body = header("Top Languages", "by code size across repositories")
    # stacked bar
    sx, sw, sy = 35, 630, 68
    body += f'<g class="grow" style="animation-delay:.2s"><clipPath id="clip"><rect x="{sx}" y="{sy}" width="{sw}" height="10" rx="5"/></clipPath><g clip-path="url(#clip)">'
    x = sx
    for i, (nm, p) in enumerate(rows):
        w = sw * p / (sum(q for _, q in rows) or 1)
        body += f'<rect x="{x:.1f}" y="{sy}" width="{w + 0.6:.1f}" height="10" fill="{PALETTE[i % 6][0]}"/>'
        x += w
    body += "</g></g>"
    y = 112
    for i, (nm, p) in enumerate(rows):
        c1, c2 = PALETTE[i % 6]
        bw = 400 * p / top
        body += (
            f'<g class="fade" style="animation-delay:{0.25 + i * 0.1:.2f}s">'
            f'<circle cx="41" cy="{y - 4}" r="4.5" fill="{c1}"/>'
            f'<text x="56" y="{y}" class="l">{escape(nm)}</text>'
            f'<rect x="200" y="{y - 10}" width="400" height="8" rx="4" fill="#1b2740"/>'
            f'<rect class="grow" style="animation-delay:{0.5 + i * 0.12:.2f}s" x="200" y="{y - 10}" width="{bw:.1f}" height="8" rx="4" fill="url(#lg{i})"/>'
            f'<text x="665" y="{y}" text-anchor="end" class="m">{p:.1f}%</text></g>'
        )
        y += 32
    grads = "".join(
        f'<linearGradient id="lg{i}" x1="0" x2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>'
        for i, (a, b) in enumerate(PALETTE)
    )
    body = f"<defs>{grads}</defs>" + body
    return wrap(W, y + 8, "Top languages", body)


# ----------------------------------------------------------------------------- main
def main():
    data = demo() if os.environ.get("DEMO") == "1" else fetch()
    os.makedirs(OUT, exist_ok=True)
    cards = {
        "overview.svg": card_overview,
        "streak.svg": card_streak,
        "activity.svg": card_activity,
        "languages.svg": card_languages,
    }
    for name, fn in cards.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(fn(data))
        print("wrote", os.path.join(OUT, name))


if __name__ == "__main__":
    main()
