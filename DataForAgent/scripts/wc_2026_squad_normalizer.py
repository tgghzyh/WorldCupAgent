"""
wc_2026_squad_normalizer.py
从维基百科 2026 世界杯球员名单 HTML 直接用队名+表格映射解析。
"""
import re, json, sys
from pathlib import Path
from bs4 import BeautifulSoup

HTML_FILE = Path(__file__).parent.parent / "data" / "raw" / "worldcup" / "wc_2026_squad_full.html"
OUT       = Path(__file__).parent.parent / "data" / "processed" / "worldcup" / "wc_2026_squad_normalized.json"

POS_MAP = {
    "门将": "Goalkeeper", "守门员": "Goalkeeper",
    "后卫": "Defender",    "中场": "Midfielder",  "前锋": "Forward",
}

def strip_tooltip(text: str) -> str:
    return re.sub(r"（[^）]*）\s*$", "", text).strip()

def parse_date_age(raw: str):
    bd  = re.search(r"\((\d{4}-\d{2}-\d{2})\)", raw)
    age = re.search(r"（(\d+)岁）", raw)
    return (bd.group(1) if bd else None), (int(age.group(1)) if age else None)

def parse_player_row(tr) -> dict | None:
    tds = tr.find_all("td")
    if len(tds) < 6:
        return None
    num_text   = tds[0].get_text(strip=True)
    if not num_text.isdigit():
        return None
    pos_raw    = tds[1].get_text(strip=True)
    name_text  = strip_tooltip(tds[2].get_text(strip=True))
    date_text  = tds[3].get_text(strip=True)
    caps_text  = tds[4].get_text(strip=True)
    goals_text = tds[5].get_text(strip=True)
    club_text  = tds[6].get_text(strip=True) if len(tds) > 6 else tds[5].get_text(strip=True)
    birth_date, age = parse_date_age(date_text)
    return {
        "number":     int(num_text),
        "name":       name_text,
        "position":   POS_MAP.get(pos_raw, pos_raw),
        "caps":       int(caps_text)   if caps_text.isdigit()  else 0,
        "goals":      int(goals_text)  if goals_text.isdigit() else 0,
        "birth_date": birth_date,
        "age":        age,
        "club":       club_text,
        "is_captain": "队长" in tds[2].get_text(),
    }

def find_coach(p_elem) -> str | None:
    text = p_elem.get_text(strip=True)
    m = re.search(r"主教练[：:]\s*(.+)", text)
    return m.group(1).strip() if m else None

def _all_cells(tr):
    return tr.find_all(["td", "th"])

def _is_squad_table(table) -> bool:
    rows = table.find_all("tr")
    if len(rows) < 3:
        return False
    for row in rows[1:]:
        cells = _all_cells(row)
        if cells and cells[0].get_text(strip=True).isdigit():
            return True
    return False

def parse_squad(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    team_entries = []
    current_group = None

    for elem in soup.body.find_all(["h2", "h3"]):
        text = elem.get_text(strip=True)
        if elem.name == "h2":
            m = re.match(r"^([A-Z]组)$", text)
            if m:
                current_group = m.group(1)
        elif elem.name == "h3" and current_group:
            team_name = text
            coach = None
            p = elem.find_next("p")
            if p:
                m2 = re.search(r"主教练[：:]\s*(.+)", p.get_text(strip=True))
                if m2:
                    coach = m2.group(1).strip()
            squad_table = None
            for tbl in elem.find_all_next("table"):
                if _is_squad_table(tbl):
                    squad_table = tbl
                    break
            team_entries.append((current_group, team_name, squad_table, coach))

    squads = {}
    for group, team, table, coach in team_entries:
        players = []
        if table:
            for row in table.find_all("tr")[2:]:
                cells = _all_cells(row)
                if not cells or not cells[0].get_text(strip=True).isdigit():
                    continue
                # cells: [0]=num, [1]=pos, [2]=name, [3]=date, [4]=caps, [5]=goals, [6]=club
                date_text  = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                caps_text  = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                goals_text = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                club_text  = cells[6].get_text(strip=True) if len(cells) > 6 else cells[5].get_text(strip=True)
                bd_m   = re.search(r"\((\d{4}-\d{2}-\d{2})\)", date_text)
                age_m  = re.search(r"（(\d+)岁）", date_text)
                players.append({
                    "number":     int(cells[0].get_text(strip=True)),
                    "name":       re.sub(r"（[^）]*）\s*$", "", cells[2].get_text(strip=True)),
                    "position":   POS_MAP.get(cells[1].get_text(strip=True), cells[1].get_text(strip=True)),
                    "caps":       int(caps_text)  if caps_text.isdigit()  else 0,
                    "goals":      int(goals_text) if goals_text.isdigit() else 0,
                    "birth_date": bd_m.group(1)   if bd_m  else None,
                    "age":        int(age_m.group(1)) if age_m else None,
                    "club":       club_text,
                    "is_captain": "队长" in cells[2].get_text(),
                })
        squads.setdefault(group, {})[team] = {"coach": coach, "players": players}

    return squads

def main():
    if not HTML_FILE.exists():
        print(f"[ERROR] HTML not found: {HTML_FILE}")
        sys.exit(1)

    html   = HTML_FILE.read_text(encoding="utf-8")
    squads = parse_squad(html)

    total_groups  = len(squads)
    total_teams   = sum(len(v) for v in squads.values())
    total_players = sum(len(v["players"]) for grp in squads.values() for v in grp.values())

    output = {
        "year":         2026,
        "source": "https://zh.wikipedia.org/zh-cn/2026%E5%B9%B4%E5%9C%8B%E9%9A%9B%E8%B6%B3%E5%8D%94%E4%B8%96%E7%95%8C%E7%9B%83%E5%8F%83%E8%B3%BD%E7%90%83%E5%93%A1%E5%90%8D%E5%96%AE",
        "generated_at": "2026-07-08",
        "stats": {
            "groups":        total_groups,
            "teams":         total_teams,
            "total_players": total_players,
        },
        "squads": squads,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Wrote {OUT}")
    print(f"  Groups:   {total_groups}")
    print(f"  Teams:    {total_teams}")
    print(f"  Players:  {total_players}")
    for g, teams in squads.items():
        print(f"  {g}: {list(teams.keys())}")

if __name__ == "__main__":
    main()
