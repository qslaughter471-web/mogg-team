import os, json, re, time, urllib.request, urllib.parse
KEY = os.environ.get("FACEIT_KEY", "")
if not KEY:
    raise SystemExit("FACEIT_KEY не задан")
PLAYERS = ["flovwyyy", "slaughter471", "-kaworuque", "hydr0ponica", "limsss-_-"]
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

def api(path):
    req = urllib.request.Request("https://open.faceit.com/data/v4" + path,
                                 headers={"Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def num(x):
    try: return float(str(x).replace(",", "."))
    except: return None

def avg(a): return sum(a) / len(a) if a else None
def fmt(x, d): return "" if x is None else f"{x:.{d}f}"

def adr_of(m):
    a = num(m.get("ADR"))
    if a is None and num(m.get("Damage")) is not None and num(m.get("Rounds")):
        a = num(m["Damage"]) / num(m["Rounds"])
    return a

data = {}
X = [[] for _ in PLAYERS]
for i, nick in enumerate(PLAYERS):
    try:
        pl = api("/players?nickname=" + urllib.parse.quote(nick))
        g = (pl.get("games") or {}).get("cs2") or {}
        raw = api(f"/players/{pl['player_id']}/games/cs2/stats?limit=30")["items"]
        allst = [x["stats"] for x in raw]
        items = allst
        if i == 0 and allst: print("Поля матча:", sorted(allst[0].keys()))
        X[i] = [[m.get("Match Id") or m.get("match_id"), m.get("Map"), str(m.get("Result")), num(m.get("K/D Ratio")), adr_of(m)] for m in allst]
        kd, hs, adr, w, K, De = [], [], [], 0, 0, 0
        for m in items:
            a = num(m.get("K/D Ratio")); kd += [a] if a is not None else []
            h = num(m.get("Headshots %")); hs += [h] if h is not None else []
            ad = num(m.get("ADR"))
            if ad is None and num(m.get("Damage")) is not None and num(m.get("Rounds")):
                ad = num(m["Damage"]) / num(m["Rounds"])
            adr += [ad] if ad is not None else []
            w += str(m.get("Result")) == "1"
            K += num(m.get("Kills")) or 0; De += num(m.get("Deaths")) or 0
        try: life = api(f"/players/{pl['player_id']}/stats/cs2").get("lifetime", {})
        except Exception: life = {}
        fkd = K / De if De else avg(kd)
        data[str(i)] = {"elo": str(g.get("faceit_elo", "")),
            "kd": fmt(num(life.get("Average K/D Ratio")) or fkd, 2),
            "adr": fmt(avg(adr), 1), "hs": fmt(avg(hs), 0),
            "wr": fmt(num(life.get("Win Rate %")), 0),
            "fkd": fmt(fkd, 2), "fw": str(sum(str(m.get("Result")) == "1" for m in allst))}
        print("OK ", nick, data[str(i)])
    except Exception as e:
        print("ERR", nick, e)

if not data:
    raise SystemExit("Нет данных, файл не тронут")
snap = {"t": time.strftime("%d.%m.%Y %H:%M"), "d": data, "x": X}
html = open(FILE, encoding="utf-8").read()
html = re.sub(r"const SNAP=.*?;\n", lambda m: "const SNAP=" + json.dumps(snap, ensure_ascii=False) + ";\n", html, count=1)
open(FILE, "w", encoding="utf-8").write(html)
print("Готово: обнови страницу", FILE)
