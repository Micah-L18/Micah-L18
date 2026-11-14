#!/usr/bin/env python3
"""Builds the animated cards for the profile README: the contribution grid and the languages bar.

Usage:  GITHUB_TOKEN=... python3 scripts/profile_cards.py <github-login> <out-dir>
        python3 scripts/profile_cards.py --sample <out-dir>     (fake data, for previewing)

Writes commit-grid.svg / commit-grid-dark.svg and languages.svg / languages-dark.svg into <out-dir>.
Standard library only.
"""
import datetime as dt
import json
import os
import random
import sys
import urllib.request

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
  }
}
"""
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

THEMES = {
    "-dark": dict(
        bg="#0d1117", border="#30363d", text="#e6edf3", muted="#8b949e", accent="#f5c518",
        outline="#0d1117", levels=["#161b22", "#12305c", "#1e5fbf", "#4c8dff", "#f5c518"]),
    "": dict(
        bg="#ffffff", border="#d0d7de", text="#1f2328", muted="#656d76", accent="#b88100",
        outline="#1f2328", levels=["#ebedf0", "#bcd4f7", "#6ea3ee", "#1e5fbf", "#e3a008"]),
}

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
W, H = 860, 250
CELL, PITCH = 11, 14
GX, GY = 62, 72            # top-left of the grid
LOOP = 12.0                # seconds for one full loop
SWEEP = 4.8                # seconds for the ball to cross the grid
BALL_R = 7
# Volleyball drawn at radius 16; scaled down where it is used.
BALL = '<clipPath id="ballclip"><circle r="16"/></clipPath><circle r="16" fill="#fbfbf6"/><g clip-path="url(#ballclip)"><path d="M1.65,-5.36 Q10.46,4.72 22.95,9.55 L23.87,4.15 Q11.38,-0.68 2.57,-10.76 Z" fill="#f5c518"/><path d="M4.25,4.86 Q-8.89,7.45 -19.32,15.85 L-15.10,19.34 Q-4.67,10.95 8.47,8.35 Z" fill="#1e5fbf"/><path d="M-5.90,2.00 Q-1.58,-10.67 -3.63,-23.90 L-8.77,-22.00 Q-6.71,-8.77 -11.03,3.91 Z" fill="#f5c518"/><path d="M0.00,0.50 Q4.32,-12.17 2.27,-25.40 M1.65,-5.36 Q10.46,4.72 22.95,9.55 M2.57,-10.76 Q11.38,-0.68 23.87,4.15 M0.00,0.50 Q8.81,10.58 21.30,15.41 M4.25,4.86 Q-8.89,7.45 -19.32,15.85 M8.47,8.35 Q-4.67,10.95 -15.10,19.34 M0.00,0.50 Q-13.13,3.09 -23.56,11.49 M-5.90,2.00 Q-1.58,-10.67 -3.63,-23.90 M-11.03,3.91 Q-6.71,-8.77 -8.77,-22.00" fill="none" stroke="#1b2a4a" stroke-width="1.1" stroke-linecap="round"/></g><circle r="16" fill="none" stroke="#1b2a4a" stroke-width="1.4000000000000001"/>'


def fetch(login):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is not set")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": "bearer " + token, "User-Agent": "profile-contrib-grid"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors") or not body.get("data", {}).get("user"):
        sys.exit("GitHub API error: %s" % json.dumps(body.get("errors", body)))
    cal = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"], LEVELS[d["contributionLevel"]])
              for d in w["contributionDays"]] for w in cal["weeks"]]
    sizes, colours = {}, {}
    for repo in body["data"]["user"]["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
            colours[name] = edge["node"]["color"]
    langs = sorted(((n, sz, colours[n]) for n, sz in sizes.items()), key=lambda x: -x[1])
    return cal["totalContributions"], weeks, langs


def sample():
    random.seed(18)
    today = dt.date.today()
    start = today - dt.timedelta(days=364 + (today.weekday() + 1) % 7)
    weeks, day = [], start
    while day <= today:
        week = []
        for _ in range(7):
            if day > today:
                break
            n = random.choice([0, 0, 0, 1, 2, 3, 5, 9]) if random.random() < 0.6 else 0
            week.append((day.isoformat(), n, 0 if n == 0 else min(4, 1 + n // 3)))
            day += dt.timedelta(days=1)
        weeks.append(week)
    langs = [("Python", 5200, "#3572A5"), ("TypeScript", 3100, "#3178c6"), ("JavaScript", 1500, "#f1e05a"),
             ("HTML", 800, "#e34c26"), ("CSS", 400, "#663399"), ("Shell", 150, "#89e051"), ("Makefile", 40, "#427819")]
    return sum(n for w in weeks for _, n, _ in w), weeks, langs


def stats(total, weeks):
    days = [d for w in weeks for d in w]
    best = max(days, key=lambda d: d[1])
    longest = run = 0
    for _, n, _ in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    best_txt = "—"
    if best[1]:
        when = dt.date.fromisoformat(best[0])
        best_txt = "%d on %s %d" % (best[1], when.strftime("%b"), when.day)
    return [
        ("CONTRIBUTIONS", "{:,}".format(total)),
        ("LONGEST STREAK", "%d day%s" % (longest, "" if longest == 1 else "s")),
        ("BEST DAY", best_txt),
        ("ACTIVE DAYS", str(sum(1 for d in days if d[1]))),
    ]


def render_grid(total, weeks, t):
    ncols = len(weeks)
    step = SWEEP / ncols
    sweep_pct = 100.0 * SWEEP / LOOP
    grid_w = ncols * PITCH
    x0 = GX - 1.5 * PITCH
    x1 = GX + grid_w + 0.5 * PITCH
    ground = GY - BALL_R - 3

    css = [
        "text{font-family:%s}" % MONO,
        ".c{animation:hop %ss linear infinite both}" % LOOP,
        ".k{animation:pop %ss linear infinite both;transform-box:fill-box;transform-origin:center}" % LOOP,
        "@keyframes hop{0%,4%,100%{transform:translateY(0)}1.5%{transform:translateY(-3px)}}",
        "@keyframes pop{0%{opacity:0;transform:scale(.3)}1.5%{opacity:1;transform:scale(1.4)}"
        "3.5%,88%{opacity:1;transform:scale(1)}94%,100%{opacity:0;transform:scale(1)}}",
        ".bx{opacity:0;animation:fly %ss linear infinite}" % LOOP,
        "@keyframes fly{0%%{opacity:1;transform:translate(%.1fpx,%dpx)}%.2f%%{opacity:1;transform:translate(%.1fpx,%dpx)}"
        "%.2f%%,99.9%%{opacity:0;transform:translate(%.1fpx,%dpx)}100%%{opacity:0;transform:translate(%.1fpx,%dpx)}}"
        % (x0, ground, sweep_pct, x1, ground, sweep_pct + 1, x1, ground, x0, ground),
        ".by{animation:bounce .375s cubic-bezier(0,0,.4,1) infinite alternate}",
        "@keyframes bounce{from{transform:translateY(0)}to{transform:translateY(-20px)}}",
        ".br{animation:spin .9s linear infinite}",
        "@keyframes spin{to{transform:rotate(360deg)}}",
    ]
    css += [".d%d,.d%d .k{animation-delay:%.3fs}" % (i, i, i * step) for i in range(ncols)]
    # People who prefer reduced motion get the finished grid with no ball.
    css.append("@media (prefers-reduced-motion:reduce){.c,.k,.bx,.by,.br{animation:none}}")

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
        'aria-label="Contribution grid: %s contributions in the last year">' % (W, H, W, H, "{:,}".format(total)),
        "<style>%s</style>" % "".join(css),
        '<rect x="1" y="1" width="%d" height="%d" rx="16" fill="%s" stroke="%s" stroke-width="2"/>'
        % (W - 2, H - 2, t["bg"], t["border"]),
        '<text x="%d" y="30" font-size="13" font-weight="700" fill="%s" letter-spacing="1.5">SEASON RECAP'
        '<tspan fill="%s" font-weight="400" letter-spacing="0"> · last 12 months</tspan></text>'
        % (GX, t["text"], t["muted"]),
    ]

    # legend, top right
    lx = GX + grid_w - 5 * PITCH - 34
    out.append('<text x="%d" y="30" font-size="11" text-anchor="end" fill="%s">less</text>' % (lx - 6, t["muted"]))
    for i, colour in enumerate(t["levels"]):
        out.append('<rect x="%d" y="20" width="%d" height="%d" rx="2.5" fill="%s"/>' % (lx + i * PITCH, CELL, CELL, colour))
    out.append('<text x="%d" y="30" font-size="11" fill="%s">more</text>' % (lx + 5 * PITCH + 4, t["muted"]))

    # weekday labels
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append('<text x="%d" y="%d" font-size="10" text-anchor="end" fill="%s">%s</text>'
                   % (GX - 8, GY + row * PITCH + 9, t["muted"], label))

    # the grid, one group per week so each column can hop as the ball passes
    last_month, last_label_col = None, -10
    for i, week in enumerate(weeks):
        x = GX + i * PITCH
        first = dt.date.fromisoformat(week[0][0])
        row0 = (first.weekday() + 1) % 7  # Sunday = row 0
        cells = []
        for j, (_, _, level) in enumerate(week):
            y = GY + (row0 + j) * PITCH
            cells.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2.5" fill="%s"/>'
                         % (x, y, CELL, CELL, t["levels"][0]))
            if level:
                cells.append('<rect class="k" x="%d" y="%d" width="%d" height="%d" rx="2.5" fill="%s"/>'
                             % (x, y, CELL, CELL, t["levels"][level]))
        out.append('<g class="c d%d">%s</g>' % (i, "".join(cells)))
        if first.month != last_month:
            if last_month is not None and i - last_label_col >= 3 and i < ncols - 1:
                out.append('<text x="%d" y="%d" font-size="10" fill="%s">%s</text>'
                           % (x, GY + 7 * PITCH + 12, t["muted"], first.strftime("%b")))
                last_label_col = i
            last_month = first.month

    # stat line
    cols = stats(total, weeks)
    for i, (label, value) in enumerate(cols):
        x = GX + i * (grid_w / len(cols))
        out.append('<text x="%.0f" y="%d" font-size="10" fill="%s" letter-spacing="1">%s</text>'
                   % (x, H - 38, t["muted"], label))
        out.append('<text x="%.0f" y="%d" font-size="16" font-weight="700" fill="%s">%s</text>'
                   % (x, H - 18, t["accent"], value))

    # the ball
    out.append('<g class="bx"><g class="by"><g class="br"><g transform="scale(%.4f)">%s</g></g></g></g>' % (BALL_R / 16.0, BALL))
    out.append("</svg>")
    return "\n".join(out)


def render_langs(langs, t):
    total = float(sum(sz for _, sz, _ in langs)) or 1.0
    top = [(n, sz / total, c or t["muted"]) for n, sz, c in langs[:6]]
    rest = 1.0 - sum(share for _, share, _ in top)
    if rest > 0.005:
        top.append(("Other", rest, t["muted"]))
    bar_w, bar_y, bar_h, h = 742, 54, 14, 130
    roll_from, roll_to, roll_y = GX + BALL_R, GX + bar_w - BALL_R, bar_y - BALL_R - 1
    turns = (roll_to - roll_from) / float(BALL_R) * 57.3
    css = [
        "text{font-family:%s}" % MONO,
        ".bar{transform-origin:%dpx 0;animation:grow %ss cubic-bezier(.2,.7,.2,1) infinite}" % (GX, LOOP),
        "@keyframes grow{0%{transform:scaleX(0);opacity:1}14%,94%{transform:scaleX(1);opacity:1}99%,100%{transform:scaleX(1);opacity:0}}",
        ".roll{opacity:0;animation:roll %ss cubic-bezier(.2,.7,.2,1) infinite}" % LOOP,
        "@keyframes roll{0%%{opacity:1;transform:translate(%dpx,%dpx) rotate(0deg)}"
        "14%%,94%%{opacity:1;transform:translate(%dpx,%dpx) rotate(%ddeg)}"
        "99%%,100%%{opacity:0;transform:translate(%dpx,%dpx) rotate(%ddeg)}}"
        % (roll_from, roll_y, roll_to, roll_y, turns, roll_to, roll_y, turns),
        "@media (prefers-reduced-motion:reduce){.bar,.roll{animation:none}}",
    ]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
        'aria-label="Languages: %s">' % (W, h, W, h, ", ".join("%s %.1f%%" % (n, s * 100) for n, s, _ in top)),
        "<style>%s</style>" % "".join(css),
        '<defs><clipPath id="pill"><rect x="%d" y="%d" width="%d" height="%d" rx="%d"/></clipPath></defs>'
        % (GX, bar_y, bar_w, bar_h, bar_h // 2),
        '<rect x="1" y="1" width="%d" height="%d" rx="16" fill="%s" stroke="%s" stroke-width="2"/>'
        % (W - 2, h - 2, t["bg"], t["border"]),
        '<text x="%d" y="30" font-size="13" font-weight="700" fill="%s" letter-spacing="1.5">LANGUAGES'
        '<tspan fill="%s" font-weight="400" letter-spacing="0"> · share of code in public repos</tspan></text>'
        % (GX, t["text"], t["muted"]),
        '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s"/>' % (GX, bar_y, bar_w, bar_h, bar_h // 2, t["levels"][0]),
        '<g clip-path="url(#pill)"><g class="bar">',
    ]
    x = float(GX)
    for _, share, colour in top:
        out.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"/>' % (x, bar_y, share * bar_w + 0.5, bar_h, colour))
        x += share * bar_w
    out.append("</g></g>")
    col = bar_w / float(max(len(top), 4))
    for i, (name, share, colour) in enumerate(top):
        lx = GX + i * col
        label = name if len(name) <= 12 else name[:11] + "…"
        out.append('<circle cx="%.0f" cy="%d" r="5" fill="%s"/>' % (lx + 5, bar_y + 37, colour))
        out.append('<text x="%.0f" y="%d" font-size="12" fill="%s">%s</text>' % (lx + 16, bar_y + 41, t["text"], label))
        out.append('<text x="%.0f" y="%d" font-size="12" fill="%s">%.1f%%</text>' % (lx + 16, bar_y + 58, t["muted"], share * 100))
    out.append('<g class="roll"><g transform="scale(%.4f)">%s</g></g>' % (BALL_R / 16.0, BALL))
    out.append("</svg>")
    return "\n".join(out)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    who, out_dir = sys.argv[1], sys.argv[2]
    total, weeks, langs = sample() if who == "--sample" else fetch(who)
    os.makedirs(out_dir, exist_ok=True)
    for suffix, theme in THEMES.items():
        cards = {"commit-grid": render_grid(total, weeks, theme)}
        if langs:
            cards["languages"] = render_langs(langs, theme)
        for name, svg in cards.items():
            with open(os.path.join(out_dir, "%s%s.svg" % (name, suffix)), "w", encoding="utf-8") as fh:
                fh.write(svg)
    print("wrote %d weeks, %d contributions, %d languages" % (len(weeks), total, len(langs)))


if __name__ == "__main__":
    main()
