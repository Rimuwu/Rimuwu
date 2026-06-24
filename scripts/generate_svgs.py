import os
import math
import base64
import urllib.request
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, date

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

COLORS = CONFIG.get("colors", {
    "background": "#000000",
    "green": "#33cc66",
    "gold": "#ffcc00",
    "white": "#ffffff",
    "red": "#ff5555",
    "header_fill": "#051a08",
    "status_active": "#55ff55",
    "status_standby": "#ff5555",
    "fallback_fill": "#111111",
    "grid_opacity": 0.06
})

GRID_OPACITY = COLORS.get("grid_opacity", 0.06)

def get_base64_image(file_path):
    if not os.path.exists(file_path):
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    with open(file_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.svg':
        return f"data:image/svg+xml;base64,{encoded}"
    elif ext == '.png':
        return f"data:image/png;base64,{encoded}"
    else:
        return f"data:image/jpeg;base64,{encoded}"

def parse_dob(dob_str):
    formats = [
        "%d %b %Y",  # 7 FEB 2101 or 07 Feb 2101
        "%d %B %Y",  # 7 February 2101
        "%Y-%m-%d",  # 2101-02-07
        "%d.%m.%Y",  # 07.02.2101
    ]
    cleaned = re.sub(r'\s+', ' ', dob_str.strip())
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass
            
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    match = re.match(r'^(\d+)\s+([a-zA-Z]+)\s+(\d+)$', cleaned)
    if match:
        d = int(match.group(1))
        m_str = match.group(2).lower()
        y = int(match.group(3))
        if m_str in months:
            m = months[m_str]
            try:
                return date(y, m, d)
            except ValueError:
                pass
    return None

def check_online_status():
    oh = CONFIG.get("online_hours", {"utc_offset": 3, "start": 10, "end": 23})
    utc_offset = oh.get("utc_offset", 3)
    start_hour = oh.get("start", 10)
    end_hour = oh.get("end", 23)
    
    # Get current UTC time, then apply offset to get local time
    now_utc = datetime.utcnow()
    now_local = now_utc + timedelta(hours=utc_offset)
    current_hour = now_local.hour
    
    is_online = start_hour <= current_hour < end_hour
    
    hours_left = 0
    if not is_online:
        if current_hour < start_hour:
            hours_left = start_hour - current_hour
        else:
            hours_left = (24 - current_hour) + start_hour
            
    return is_online, hours_left

def get_system_online_xml(is_online):
    if is_online:
        return f"""<svg x="660" y="15" width="120" height="20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 20">
  <style>
    @keyframes blink {{
      0%, 100% {{ opacity: 0.15; }}
      50% {{ opacity: 1; }}
    }}
    .blinking-text {{
      font-family: monospace;
      font-weight: bold;
      fill: {COLORS['green']};
      font-size: 14px;
      animation: blink 1.5s steps(2, start) infinite;
    }}
  </style>
  <text x="5" y="14" class="blinking-text">SYSTEM ONLINE</text>
</svg>"""
    else:
        return f"""<svg x="660" y="15" width="120" height="20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 20">
  <style>
    .offline-text {{
      font-family: monospace;
      font-weight: bold;
      fill: {COLORS['red']};
      font-size: 14px;
      opacity: 0.6;
    }}
  </style>
  <text x="5" y="14" class="offline-text">SYSTEM STANDBY</text>
</svg>"""

def make_decryption_svg(label, key, rest_of_text, y_pos, start_time, label_color="text-green", text_color="text-white", rest_color="text-green"):
    step_dur = 0.05
    prefix_delay = 0.5
    full_string = key + rest_of_text
    n = len(full_string)
    xml = []
    
    # 1. Initial state (empty)
    if start_time == 0:
        xml.append(f'    <text x="0" y="{y_pos}" class="monospace {label_color}" font-size="13" font-weight="bold" style="animation: fadeOut {prefix_delay:.2f}s forwards;">'
                   f'{label}</text>')
    else:
        xml.append(f'    <text x="0" y="{y_pos}" class="monospace {label_color}" font-size="13" font-weight="bold" style="animation: fadeOut {prefix_delay:.2f}s forwards; animation-delay: {start_time:.2f}s;">'
                   f'{label}</text>')
        
    # 2. Intermediate states
    for i in range(1, n):
        revealed_key = full_string[:min(i, len(key))]
        revealed_rest = full_string[len(key):max(i, len(key))]
        
        xml.append(f'    <text x="0" y="{y_pos}" class="monospace {label_color}" font-size="13" font-weight="bold" style="animation: flashStep {step_dur:.2f}s forwards; animation-delay: {start_time + prefix_delay + (i - 1) * step_dur:.2f}s; opacity: 0;">'
                   f'{label}<tspan class="{text_color}">{xml_escape(revealed_key)}</tspan>'
                   f'<tspan class="{rest_color}">{xml_escape(revealed_rest)}</tspan></text>')
        
    # 3. Final persistent state
    final_delay = start_time + prefix_delay + (n - 1) * step_dur
    xml.append(f'    <text x="0" y="{y_pos}" class="monospace {label_color}" font-size="13" font-weight="bold" style="animation: fadeInPersistent 0.1s forwards; animation-delay: {final_delay:.2f}s; opacity: 0;">'
               f'{label}<tspan class="{text_color}">{xml_escape(key)}</tspan><tspan class="{rest_color}">{xml_escape(rest_of_text)}</tspan></text>')
    
    total_duration = prefix_delay + (n - 1) * step_dur
    return "\n".join(xml), total_duration

def get_dots_placeholder_xml(width, height):
    cx = width / 2
    cy = height / 2
    spacing = 16
    size = 7
    xml = [
        f'  <rect x="2" y="2" width="{width - 4}" height="{height - 4}" fill="{COLORS["background"]}" />',
        f'  <rect x="{cx - spacing - size/2:.1f}" y="{cy - size/2:.1f}" width="{size}" height="{size}" fill="{COLORS["green"]}" style="animation: blinkDot 1.4s infinite; animation-delay: 0.0s;" />',
        f'  <rect x="{cx - size/2:.1f}" y="{cy - size/2:.1f}" width="{size}" height="{size}" fill="{COLORS["green"]}" style="animation: blinkDot 1.4s infinite; animation-delay: 0.2s;" />',
        f'  <rect x="{cx + spacing - size/2:.1f}" y="{cy - size/2:.1f}" width="{size}" height="{size}" fill="{COLORS["green"]}" style="animation: blinkDot 1.4s infinite; animation-delay: 0.4s;" />'
    ]
    xml_str = "\n".join(xml)
    return f"""<g>
{xml_str}
</g>"""

def generate_globe_html(x, y):
    import math

    R = 48
    cx = 60
    cy = 60
    TILT = 0.65
    STEPS = 60
    FRAMES = 36
    DURATION = "24s"

    green = COLORS['green']

    def proj(lng, lat, rot):
        x0 = R * math.cos(lat) * math.cos(lng)
        y0 = R * math.sin(lat)
        z0 = R * math.cos(lat) * math.sin(lng)
        x1 = x0 * math.cos(rot) + z0 * math.sin(rot)
        y1 = y0
        z1 = -x0 * math.sin(rot) + z0 * math.cos(rot)
        y2 = y1 * math.cos(TILT) - z1 * math.sin(TILT)
        z2 = y1 * math.sin(TILT) + z1 * math.cos(TILT)
        return cx + x1, cy - y2, z2

    def make_d(pts):
        # Всегда только M+L, никогда не меняем команду — структура одинакова во всех кадрах
        parts = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
        for px, py, _ in pts[1:]:
            parts.append(f"L{px:.1f},{py:.1f}")
        return "".join(parts)

    def make_d_front(pts):
        # Только видимая часть — но через clip, не через смену команд
        # Передняя полусфера (z>=0) — полная opacity
        # Задняя (z<0) — рисуем тоже L, но будет отдельный path с меньшей opacity
        parts = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
        for px, py, _ in pts[1:]:
            parts.append(f"L{px:.1f},{py:.1f}")
        return "".join(parts)

    def make_frame(rot):
        paths = []
        for m in range(12):
            lng = (m / 12) * math.pi * 2
            pts = [proj(lng, -math.pi/2 + math.pi * i / STEPS, rot) for i in range(STEPS + 1)]
            paths.append(make_d(pts))
        for p in range(1, 8):
            lat = -math.pi/2 + math.pi * p / 8
            pts = [proj(math.pi * 2 * i / STEPS, lat, rot) for i in range(STEPS + 1)]
            paths.append(make_d(pts))
        return paths

    all_frames = [make_frame((f / FRAMES) * math.pi * 2) for f in range(FRAMES)]

    # Для каждого пути определяем среднюю видимость по всем кадрам —
    # нам нужно два слоя: задний (тусклый) и передний (яркий)
    # Передний слой — clipPath по окружности с маской левой/правой полусферы не работает в SVG анимации
    # Поэтому делаем два одинаковых пути: один тусклый (вся линия), один яркий но с clipPath

    # ClipPath — полукруг передней полусферы (статичный, т.к. граница всегда — вертикальный эллипс)
    # При наклоне TILT граница — эллипс, аппроксимируем через rect или ellipse
    # Проще всего: clips не анимируются, поэтому используем градиент opacity через mask

    # Финальное решение: два слоя path с одинаковой структурой d
    # layer 1: opacity 0.08 (задняя полусфера просвечивает)  
    # layer 2: тот же path но с clipPath = передняя полусфера (эллипс)
    # clipPath не требует анимации — граница видимости это всегда вертикальный эллипс по центру

    num_paths = 19
    paths_xml = ""

    # clipPath: передняя полусфера = левая половина окружности повёрнутая с учётом tilt
    # Граница — эллипс rx=R*sin(tilt_angle_offset), но проще — просто rect правая половина
    # На самом деле граница видимости при вращении вокруг Y — это вертикальный эллипс
    # с rx зависящим от tilt. При TILT=0.65 рад граница чуть наклонена.
    # Аппроксимация: ellipse cx=60 cy=60 rx=1 ry=48 — вертикальная линия, делим пополам
    # Для простоты: clip = rect x=cx, y=0, w=R+10, h=120 (правая половина видна)
    # Но это статично и не учитывает наклон — зато структура d не меняется!

    clip_xml = f"""<defs>
    <clipPath id="globe-front-{x}-{y}">
        <ellipse cx="{cx}" cy="{cy}" rx="{R}" ry="{R}" />
    </clipPath>
</defs>"""

    for pidx in range(num_paths):
        is_meridian = pidx < 12
        is_eq = (not is_meridian) and (pidx - 12 + 1 == 4)
        op_back = "0.1" if is_eq else "0.07"
        op_front = "0.75" if is_eq else ("0.45" if is_meridian else "0.28")
        sw = "1.1" if is_eq else ("0.7" if is_meridian else "0.6")

        vals = [frame[pidx] for frame in all_frames] + [all_frames[0][pidx]]
        values_str = ";".join(vals)

        # Задний слой — тусклый, вся линия
        paths_xml += f"""
    <path fill="none" stroke="{green}" stroke-width="{sw}" opacity="{op_back}">
        <animate attributeName="d" dur="{DURATION}" repeatCount="indefinite"
            calcMode="linear" values="{values_str}"/>
    </path>"""

        # Передний слой — яркий, обрезан по окружности (clipPath убирает выход за пределы шара)
        paths_xml += f"""
    <path fill="none" stroke="{green}" stroke-width="{sw}" opacity="{op_front}" clip-path="url(#globe-front-{x}-{y})">
        <animate attributeName="d" dur="{DURATION}" repeatCount="indefinite"
            calcMode="linear" values="{values_str}"/>
    </path>"""

    return f"""<g transform="translate({x}, {y})">
    {clip_xml}
    <circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{green}" stroke-width="1.5" opacity="0.9"/>
    {paths_xml}
</g>"""

def parse_github_stats_and_chart():
    # 1. Default fallback datasets and values
    commits = "1465"
    repos = "24"
    joined = "7 years ago"
    prs = "115"
    issues = "6"
    stars = "82"
    contribs = "15"
    rank = "A-"
    
    top_repos = [
        ("DinoGochi-WebOpen", 43, "Python"),
        ("SMM.web", 18, "Vue"),
        ("SPS-Shortly-PartyStory", 15, "GDScript"),
        ("vibe-preparation", 2, "JavaScript")
    ]
    
    languages = [
        ("Python", 74.81, "#3572A5"),
        ("Vue", 10.06, "#41b883"),
        ("GDScript", 9.74, "#478CBF"),
        ("JavaScript", 3.83, "#f1e05a"),
        ("C#", 0.95, "#178600"),
        ("CSS", 0.61, "#663399")
    ]
    
    # Generate mock weeks contributions (7 years, 52 weeks = 364 weeks)
    # Using random walk to avoid repetitive wave look
    import random
    random.seed(42)
    all_weeks_contributions = []
    all_weeks_dates = []
    start_dt = datetime.now() - timedelta(weeks=364)
    
    curr_val = 15
    for idx in range(364):
        dt = start_dt + timedelta(weeks=idx)
        change = random.choice([-6, -3, -1, 0, 1, 3, 5, 8])
        curr_val = max(0, min(80, curr_val + change))
        if dt.month == 12 and dt.day > 20:
            val = int(curr_val * 0.15)
        else:
            val = curr_val
        all_weeks_contributions.append(val)
        all_weeks_dates.append(dt)
        
    token = os.environ.get("ST_TOKEN") or os.environ.get("GITHUB_TOKEN")
    username = CONFIG["profile"]["name"]
    
    if token:
        try:
            req_headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Rimuwu-Profile-App"
            }
            
            # Fetch user details
            user_url = f"https://api.github.com/users/{username}"
            req = urllib.request.Request(user_url, headers=req_headers)
            created_year = datetime.now().year - 7
            with urllib.request.urlopen(req, timeout=5) as res:
                user_data = json.loads(res.read().decode("utf-8"))
                repos = str(user_data.get("public_repos", repos))
                created_at_str = user_data.get("created_at")
                if created_at_str:
                    created_year = datetime.strptime(created_at_str[:10], "%Y-%m-%d").year
                    years_active = datetime.now().year - created_year
                    joined = f"{years_active} years ago"
            
            # GraphQL query
            current_year = datetime.now().year
            year_queries = []
            for yr in range(created_year, current_year + 1):
                year_queries.append(f"""
                y{yr}: contributionsCollection(from: "{yr}-01-01T00:00:00Z", to: "{yr}-12-31T23:59:59Z") {{
                  contributionCalendar {{
                    totalContributions
                    weeks {{
                      contributionDays {{
                        contributionCount
                        date
                      }}
                    }}
                  }}
                }}
                """)
            year_queries_str = "\n".join(year_queries)

            query = f"""
            query($username: String!) {{
              user(login: $username) {{
                issues {{
                  totalCount
                }}
                pullRequests {{
                  totalCount
                }}
                repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {{field: STARGAZERS, direction: DESC}}) {{
                  nodes {{
                    name
                    stargazerCount
                    primaryLanguage {{
                      name
                      color
                    }}
                    languages(first: 10, orderBy: {{field: SIZE, direction: DESC}}) {{
                      edges {{
                        size
                        node {{
                          name
                          color
                        }}
                      }}
                    }}
                    defaultBranchRef {{
                      target {{
                        ... on Commit {{
                          history {{
                            totalCount
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                {year_queries_str}
              }}
            }}
            """
            
            gql_data = json.dumps({"query": query, "variables": {"username": username}}).encode("utf-8")
            gql_req = urllib.request.Request("https://api.github.com/graphql", data=gql_data, headers=req_headers, method="POST")
            with urllib.request.urlopen(gql_req, timeout=5) as res:
                result = json.loads(res.read().decode("utf-8"))
                user_res = result.get("data", {}).get("user", {})
                if user_res:
                    issues = str(user_res.get("issues", {}).get("totalCount", issues))
                    prs = str(user_res.get("pullRequests", {}).get("totalCount", prs))
                    
                    repos_nodes = user_res.get("repositories", {}).get("nodes", [])
                    total_stars = sum(r.get("stargazerCount", 0) for r in repos_nodes)
                    stars = str(total_stars)
                    
                    total_commits = 0
                    for r in repos_nodes:
                        ref = r.get("defaultBranchRef")
                        if ref:
                            target = ref.get("target")
                            if target:
                                total_commits += target.get("history", {}).get("totalCount", 0)
                                
                    langs_agg = {}
                    for r in repos_nodes:
                        edges = r.get("languages", {}).get("edges", [])
                        for edge in edges:
                            l_name = edge["node"]["name"]
                            l_color = edge["node"].get("color") or "#888888"
                            l_size = edge["size"]
                            if l_name not in langs_agg:
                                langs_agg[l_name] = {"size": 0, "color": l_color}
                            langs_agg[l_name]["size"] += l_size
                            
                    total_lang_size = sum(info["size"] for info in langs_agg.values())
                    langs_list = []
                    for name, info in langs_agg.items():
                        pct = (info["size"] / total_lang_size) * 100 if total_lang_size else 0
                        langs_list.append((name, pct, info["color"]))
                    langs_list.sort(key=lambda x: x[1], reverse=True)
                    if langs_list:
                        languages = langs_list
                        
                    sorted_repos = sorted(repos_nodes, key=lambda x: x.get("stargazerCount", 0), reverse=True)
                    top_repos_list = []
                    for r in sorted_repos[:4]:
                        r_name = r.get("name")
                        r_stars = r.get("stargazerCount", 0)
                        r_lang = r.get("primaryLanguage")
                        r_lang_name = r_lang.get("name") if r_lang else "Unknown"
                        top_repos_list.append((r_name, r_stars, r_lang_name))
                    if top_repos_list:
                        top_repos = top_repos_list
                        
                    parsed_contributions = []
                    parsed_dates = []
                    total_calendar_commits = 0
                    for yr in range(created_year, current_year + 1):
                        cal = user_res.get(f"y{yr}", {}).get("contributionCalendar", {})
                        total_calendar_commits += cal.get("totalContributions", 0)
                        weeks_data = cal.get("weeks", [])
                        for w in weeks_data:
                            days = w.get("contributionDays", [])
                            if days:
                                parsed_contributions.append(sum(d.get("contributionCount", 0) for d in days))
                                parsed_dates.append(datetime.strptime(days[0]["date"], "%Y-%m-%d"))
                                
                    if parsed_contributions:
                        all_weeks_contributions = parsed_contributions
                        all_weeks_dates = parsed_dates
                        
                    if total_commits == 0:
                        total_commits = total_calendar_commits
                    if total_commits > 0:
                        commits = str(total_commits)
                        
                    rank_score = total_stars * 10 + int(commits) * 0.5 + int(prs) * 2 + int(issues) * 0.5 + len(repos_nodes) * 5
                    if rank_score > 5000: rank = "S"
                    elif rank_score > 3000: rank = "A+"
                    elif rank_score > 1000: rank = "A"
                    elif rank_score > 500: rank = "A-"
                    elif rank_score > 250: rank = "B+"
                    elif rank_score > 100: rank = "B"
                    else: rank = "C"
                    
        except Exception as e:
            print(f"Error fetching live GitHub data: {e}")

    commits = commits.replace(",", "")
    prs = prs.replace(",", "")
    issues = issues.replace(",", "")
    stars = stars.replace(",", "")
    contribs = repos

    return (
        commits, repos, joined, prs, issues, stars, contribs, rank,
        top_repos, languages,
        all_weeks_contributions, all_weeks_dates
    )

def get_grid_reveal_xml(width, height, start_delay):
    cols, rows = 4, 4
    cell_w = (width - 4) / cols
    cell_h = (height - 4) / rows
    # Predefined shuffle pattern for 4x4 grid cells
    pattern = [
        [2, 1, 5, 3],
        [6, 0, 7, 2],
        [4, 7, 1, 6],
        [3, 5, 2, 4]
    ]
    xml_cells = []
    for r in range(rows):
        for c in range(cols):
            x = 2 + c * cell_w
            y = 2 + r * cell_h
            w = cell_w + 0.5
            h = cell_h + 0.5
            cell_delay = pattern[r][c] * 0.08  # Max delay is 7 * 0.08 = 0.56s
            xml_cells.append(
                f'  <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{COLORS["background"]}" '
                f'style="animation: fadeOutCell 0.25s forwards; animation-delay: {start_delay + cell_delay:.2f}s;" />'
            )
    
    cells_str = "\n".join(xml_cells)
    return f"""<g style="animation: fadeInPersistent 0.05s forwards; animation-delay: {start_delay:.2f}s; opacity: 0;">
{cells_str}
</g>"""

def get_inline_svg_xml(file_path, x, y, width, height):
    if not os.path.exists(file_path):
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{COLORS["fallback_fill"]}" stroke="{COLORS["green"]}" stroke-width="2"/>'
    try:
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        tree = ET.parse(file_path)
        root = tree.getroot()
        if root.tag.endswith('svg'):
            root.set('x', str(x))
            root.set('y', str(y))
            root.set('width', str(width))
            root.set('height', str(height))
            
            if 'viewBox' not in root.attrib:
                w = root.get('width', '').replace('px', '').strip()
                h = root.get('height', '').replace('px', '').strip()
                if w and h:
                    root.set('viewBox', f"0 0 {w} {h}")
                    
            xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
            xml_str = re.sub(r'<\?xml[^>]*\?>', '', xml_str)
            return xml_str
    except Exception as e:
        print(f"Error inlining SVG {file_path}: {e}")
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="#111111" stroke="#33cc66" stroke-width="2"/>'

def fetch_badge_base64(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            encoded = base64.b64encode(data).decode('utf-8')
            svg_text = data.decode('utf-8', errors='ignore')
            width_match = re.search(r'<svg[^>]+width="([^"]+)"', svg_text)
            width = int(float(width_match.group(1))) if width_match else 110
            return f"data:image/svg+xml;base64,{encoded}", width
    except Exception as e:
        print(f"Error fetching badge {url}: {e}")
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", 110

def xml_escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

def wrap_log_text(title, text, max_chars=45):
    title_len = len(title)
    first_line_limit = max(15, max_chars - title_len)
    
    words = text.split(' ')
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        limit = first_line_limit if not lines else max_chars
        if current_length + len(word) + (1 if current_line else 0) > limit:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + (1 if len(current_line) > 1 else 0)
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def generate_header_xml_elements():
    top_b64 = get_base64_image("images/top.jfif")
    left_b64 = get_base64_image("images/left.jpg")
    down_b64 = get_base64_image("images/down.jpg")
    
    is_online, hours_left = check_online_status()
    system_online_xml = get_system_online_xml(is_online)

    profile = CONFIG["profile"]
    log_h_size = CONFIG["fonts"]["log_header_font_size"]
    log_t_size = CONFIG["fonts"]["log_text_font_size"]
    citizen_id_esc = xml_escape(profile["citizen_id"])
    name_esc = xml_escape(profile["name"])
    name_real_esc = xml_escape(profile["name_real"])
    dept_esc = xml_escape(profile["dept"])
    dept_desc_esc = xml_escape(profile["dept_desc"])
    
    # Calculate online status & text
    if is_online:
        status_text = "ACTIVE"
        status_color = COLORS["status_active"]
    else:
        status_text = f"STANDBY ({hours_left}h remaining)"
        status_color = COLORS["status_standby"]
        
    status_esc = xml_escape(status_text)
    
    # Calculate DOB suffix
    dob_esc = xml_escape(profile["dob"])
    pob_esc = xml_escape(profile["pob"])
    
    today = date.today()
    dob_parsed = parse_dob(profile["dob"])
    dob_suffix = ""
    if dob_parsed:
        diff_days = (today - dob_parsed).days
        if diff_days >= 0:
            dob_suffix = f" ({diff_days:,} days ago)"
        else:
            dob_suffix = f" (in {-diff_days:,} days)"
    dob_suffix_esc = xml_escape(dob_suffix)

    # Sequential typing animations
    name_xml, name_dur = make_decryption_svg("NAME: ", name_esc, f" ({name_real_esc})", 60, 0.0, rest_color="text-green")
    
    dept_start = name_dur + 0.3
    dept_xml, dept_dur = make_decryption_svg("DEPT: ", dept_esc, f" ({dept_desc_esc})", 80, dept_start, text_color="text-red", rest_color="text-green")
    
    dob_start = dept_start + dept_dur + 0.3
    dob_xml, dob_dur = make_decryption_svg("DATE OF BIRTH: ", dob_esc, dob_suffix_esc, 130, dob_start, text_color="text-white", rest_color="text-green-dim")
    
    pob_start = dob_start + dob_dur + 0.3
    pob_xml, pob_dur = make_decryption_svg("BIRTH PLACE: ", pob_esc, "", 150, pob_start)

    image_load_start = 0.0
    log_delay = pob_start + pob_dur + 0.5

    # Generate logs HTML with automatic line wrapping, timestamps, and sequential fade-ins
    logs_html = ""
    y_start = 218
    for item in profile["logs"]:
        timestamp = item.get("timestamp", "2128-06-24 12:00:00")
        timestamp_esc = xml_escape(timestamp)
        logs_html += f'  <g style="animation: fadeInPersistent 0.4s forwards; animation-delay: {log_delay:.2f}s; opacity: 0;">\n'
        logs_html += f'    <text x="0" y="{y_start}" class="monospace text-green-dim" font-size="{log_t_size}">[{timestamp_esc}]</text>\n'
        y_start += 16
        
        title_esc = xml_escape(item["title"])
        body_lines = wrap_log_text(item["title"], item["text"], max_chars=45)
        for idx, line in enumerate(body_lines):
            line_esc = xml_escape(line)
            if idx == 0:
                logs_html += f'    <text x="0" y="{y_start}" class="monospace text-gold" font-size="{log_t_size}">&gt; <tspan class="text-green">{title_esc}</tspan> {line_esc}</text>\n'
            else:
                logs_html += f'    <text x="16" y="{y_start}" class="monospace text-gold" font-size="{log_t_size}">{line_esc}</text>\n'
            y_start += 16
        logs_html += '  </g>\n'
        y_start += 12 # Gap between items
        log_delay += 0.5 # Delay gap before next log appears

    # Three blinking dots animations for the biometric placeholders
    spec_top = get_dots_placeholder_xml(320, 230)
    spec_left = get_dots_placeholder_xml(155, 110)
    spec_right = get_dots_placeholder_xml(155, 110)

    # Grid reveal masks overlaying the images
    grid_top = get_grid_reveal_xml(320, 230, image_load_start)
    grid_left = get_grid_reveal_xml(155, 110, image_load_start + 0.7)
    grid_right = get_grid_reveal_xml(155, 110, image_load_start + 1.4)

    return f"""  <!-- Header Bar -->
  <rect x="2" y="2" width="796" height="40" fill="{COLORS['header_fill']}" stroke="{COLORS['green']}" stroke-width="2"/>
  <text x="20" y="26" class="monospace text-green" font-size="14" font-weight="bold">⚠️ WEYLAND-AW CORP</text>
  <text x="400" y="26" class="monospace text-green" font-size="14" font-weight="bold" text-anchor="middle">PLANETS AFFAIRS DATABASE</text>
  {system_online_xml}

  <!-- Left Column: Citizen Data (Manually Wrapped Logs) -->
  <g transform="translate(20, 65)">
    <text x="0" y="20" class="monospace text-gold" font-size="18" font-weight="bold">CITIZEN ID: {citizen_id_esc}</text>
    <text x="0" y="35" class="monospace text-green" font-size="12">----------------------------------------</text>
    
    {name_xml}
    {dept_xml}
    <text x="0" y="100" class="monospace text-green" font-size="13" font-weight="bold">STATUS: <tspan fill="{status_color}">{status_esc}</tspan></text>
    
    {dob_xml}
    {pob_xml}
    
    <text x="0" y="190" class="monospace text-gold" font-size="{log_h_size}" font-weight="bold">SYSTEM LOGS / OBJECTIVES:</text>
{logs_html}  </g>

  <!-- Right Column: Biometric Images (More Square Aspect Ratios) -->
  <g transform="translate(460, 60)">
    <!-- Main Photo (Taller / 4:3 Ratio) -->
    <g>
      {spec_top}
      <rect x="0" y="0" width="320" height="230" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
      <image href="{top_b64}" x="2" y="2" width="316" height="226" preserveAspectRatio="xMidYMid slice" style="animation: fadeInPersistent 0.1s forwards; animation-delay: {image_load_start:.2f}s; opacity: 0;" />
      {grid_top}
    </g>

    <!-- Bottom Left Photo -->
    <g transform="translate(0, 240)">
      {spec_left}
      <rect x="0" y="0" width="155" height="110" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
      <image href="{left_b64}" x="2" y="2" width="151" height="106" preserveAspectRatio="xMidYMid slice" style="animation: fadeInPersistent 0.1s forwards; animation-delay: {image_load_start + 0.7:.2f}s; opacity: 0;" />
      {grid_left}
    </g>

    <!-- Bottom Right Photo -->
    <g transform="translate(165, 240)">
      {spec_right}
      <rect x="0" y="0" width="155" height="110" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
      <image href="{down_b64}" x="2" y="2" width="151" height="106" preserveAspectRatio="xMidYMid slice" style="animation: fadeInPersistent 0.1s forwards; animation-delay: {image_load_start + 1.4:.2f}s; opacity: 0;" />
      {grid_right}
    </g>

    <!-- Caption -->
    <text x="160" y="365" class="monospace text-green" font-size="12" font-weight="bold" text-anchor="middle">SUBJECT BIOMETRIC IMAGES</text>
  </g>""", top_b64, left_b64, down_b64

def generate_stack_xml_elements(embeds):
    # Left column: Badges
    badges_xml = ""
    x_offset = 0
    y_offset = 0
    for i, (b64, w) in enumerate(embeds):
        if i > 0 and (x_offset + w > 520):
            x_offset = 0
            y_offset += 38
        
        badges_xml += f'    <image href="{b64}" x="{x_offset}" y="{y_offset}" width="{w}" height="28" class="badge-anim" style="animation-delay: {i * 0.1:.1f}s;" />\n'
        x_offset += w + 8

    # Generate dense meridians (every 15 degrees: 0, 15, ..., 165)
    meridians = []
    for deg in range(0, 180, 15):
        meridians.append(
            f'        <ellipse cx="0" cy="0" rx="45" ry="45" fill="none" stroke="{COLORS["green"]}" stroke-width="0.8" opacity="0.45" style="transform: rotateY({deg}deg);" />'
        )
    meridians_xml = "\n".join(meridians)

    # Generate dense parallels (11 horizontal circles)
    import math
    parallels = []
    for y_val in [0, 8, -8, 16, -16, 24, -24, 32, -32, 40, -40]:
        rx_val = math.sqrt(45**2 - y_val**2)
        parallels.append(
            f'        <ellipse cx="0" cy="0" rx="{rx_val:.1f}" ry="{rx_val:.1f}" fill="none" stroke="{COLORS["green"]}" stroke-width="0.5" opacity="0.25" style="transform: translateY({y_val}px) rotateX(90deg);" />'
        )
    parallels_xml = "\n".join(parallels)

    globe_fo = generate_globe_html(136, 0)

    elements = f"""  <!-- Section Header -->
  <rect x="2" y="0" width="796" height="30" fill="{COLORS['header_fill']}" stroke="{COLORS['green']}" stroke-width="2"/>
  <text x="20" y="21" class="monospace text-gold" font-size="16" font-weight="bold">[ ACTIVE MODULES &amp; TOOLKITS ]</text>

  <!-- Left Column: Badges Grid Layout -->
  <g transform="translate(20, 42)">
{badges_xml}  </g>

  <!-- Right Column: Planetary Scanner Widget -->
  <g transform="translate(540, 35)">
    {globe_fo}
    <text x="5" y="20" class="monospace text-green-dim" font-size="9" font-weight="bold">PLANET SCANNER [ACTIVE]</text>
    <text x="5" y="40" class="monospace text-green-dim" font-size="7">GEO: <tspan class="text-white">35°42&apos;08.1&quot;N 139°46&apos;28.2&quot;E</tspan></text>
    <text x="5" y="60" class="monospace text-green-dim" font-size="8">TARGET: OHTORI PARKING TOWER</text>
    <text x="5" y="74" class="monospace text-green-dim" font-size="7.5">LOC: AKIHABARA, TOKYO</text>
  </g>"""
    return elements

def generate_metrics_xml_elements():
    (
        commits, repos, joined, prs, issues, stars, contribs, rank,
        top_repos, languages,
        all_weeks_contributions, all_weeks_dates
    ) = parse_github_stats_and_chart()

    # ── Chart path builder ─────────────────────────────────────────────
    def build_paths(vals, w, h):
        """Return (fill_d, stroke_d) SVG path strings."""
        if not vals or len(vals) < 2:
            return f"M0,{h} L{w},{h} Z", f"M0,{h} L{w},{h}"
        max_v = max(vals) or 1
        n = len(vals)
        pts = [(i * w / (n - 1), h - (v / max_v) * (h * 0.88))
               for i, v in enumerate(vals)]
        stroke_parts = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"] + [
            f"L{x:.1f},{y:.1f}" for x, y in pts[1:]
        ]
        stroke_d = "".join(stroke_parts)
        fill_d = (stroke_d + f" L{pts[-1][0]:.1f},{h:.1f}"
                  + f" L{pts[0][0]:.1f},{h:.1f} Z")
        return fill_d, stroke_d

    # ── Graph 1: last 52 weeks (this year) ────────────────────────────
    G1_W, G1_H = 345, 100
    g1_vals  = (all_weeks_contributions[-52:] if len(all_weeks_contributions) >= 52
                else all_weeks_contributions)
    g1_dates = (all_weeks_dates[-52:] if len(all_weeks_dates) >= 52
                else all_weeks_dates)
    g1_fill, g1_stroke = build_paths(g1_vals, G1_W, G1_H)

    # ── Graph 2: all time ──────────────────────────────────────────────
    G2_W, G2_H = 740, 120
    g2_fill, g2_stroke = build_paths(all_weeks_contributions, G2_W, G2_H)

    # ── Month labels for Graph 1 (no overlap: min 4 weeks apart) ──────
    def make_month_labels(dates, w, chart_h):
        if not dates:
            return ""
        n = len(dates)
        out, last_m, last_i = [], -1, -999
        for i, dt in enumerate(dates):
            if dt.month != last_m and (i - last_i) >= 4:
                x = i * w / (n - 1) if n > 1 else 0
                out.append(
                    f'<text x="{x:.1f}" y="{chart_h + 15}"'
                    f' class="monospace text-green-dim" font-size="8"'
                    f' text-anchor="middle">{dt.strftime("%b")}</text>'
                )
                last_m, last_i = dt.month, i
        return "\n        ".join(out)

    # ── Year labels for Graph 2 ────────────────────────────────────────
    def make_year_labels(dates, w, chart_h):
        if not dates:
            return ""
        n = len(dates)
        out, last_y = [], -1
        for i, dt in enumerate(dates):
            if dt.year != last_y:
                x = i * w / (n - 1) if n > 1 else 0
                out.append(
                    f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{chart_h}"'
                    f' stroke="{COLORS["green"]}" stroke-width="0.5"'
                    f' opacity="0.18" stroke-dasharray="2 2"/>'
                )
                out.append(
                    f'<text x="{x + 2:.1f}" y="{chart_h + 13}"'
                    f' class="monospace text-green-dim" font-size="7.5"'
                    f' text-anchor="start">{dt.year}</text>'
                )
                last_y = dt.year
        return "\n        ".join(out)

    g1_months_xml = make_month_labels(g1_dates, G1_W, G1_H)
    g2_years_xml  = make_year_labels(all_weeks_dates, G2_W, G2_H)

    # ── Language # bars (up to 5 langs, full-width) ────────────────────
    BAR_CHARS = 40
    BAR_W     = 335
    top_langs = languages[:5]
    langs_xml = ""
    for idx, (l_name, l_pct, l_col) in enumerate(top_langs):
        y_lbl  = 46 + idx * 23
        y_bar  = y_lbl + 11
        filled = max(0, min(BAR_CHARS, round((l_pct / 100.0) * BAR_CHARS)))
        empty  = BAR_CHARS - filled
        hash_s = "#" * filled
        dot_s  = ":" * empty
        langs_xml += (
            f'\n      <text x="20" y="{y_lbl}" font-size="9.5"'
            f' class="monospace text-white">{xml_escape(l_name)}'
            f' <tspan fill="{l_col}" font-weight="bold">({l_pct:.1f}%)</tspan></text>'
            f'\n      <text x="20" y="{y_bar}" font-size="9"'
            f' font-family="monospace, Courier, fixed"'
            f' textLength="{BAR_W}" lengthAdjust="spacing">'
            f'<tspan fill="{l_col}">{hash_s}</tspan>'
            f'<tspan fill="{COLORS["green"]}" opacity="0.18">{dot_s}</tspan></text>'
        )

    # ── Top Repositories ───────────────────────────────────────────────
    def trunc(name, mx=20):
        return name[:mx] + ".." if len(name) > mx else name

    repos_xml = ""
    for ri in range(4):
        if ri < len(top_repos):
            rname  = xml_escape(trunc(top_repos[ri][0]))
            rstars = top_repos[ri][1]
            rlang  = xml_escape(top_repos[ri][2] or "Unknown")
        else:
            rname, rstars, rlang = "-", 0, "-"
        y_r = 50 + ri * 29
        repos_xml += (
            f'\n      <text x="20" y="{y_r}" font-size="10"'
            f' class="monospace text-green" font-weight="bold">{rname}</text>'
            f'\n      <text x="238" y="{y_r}" font-size="10"'
            f' class="monospace text-gold">&#x2605; {rstars}</text>'
            f'\n      <text x="285" y="{y_r}" font-size="9"'
            f' class="monospace text-white" opacity="0.55">[{rlang}]</text>'
        )

    # Layout: header=30|pad=12|row1=200|gap=12|row2=160|gap=12|row3=207|pad=12 = 645
    return f"""  <!-- Section Header -->
  <rect x="2" y="0" width="796" height="30" fill="{COLORS['header_fill']}" stroke="{COLORS['green']}" stroke-width="2"/>
  <text x="20" y="21" class="monospace text-gold" font-size="16" font-weight="bold">[ BIOMETRIC METRICS &amp; PERFORMANCE GRAPH ]</text>

  <!-- ═══ ROW 1: GitHub Stats (left) + Graph 1 This Year (right) ═══ -->
  <rect x="15" y="42" width="375" height="200" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
  <g transform="translate(15,42)">
    <g transform="translate(15,28)" font-size="11" class="monospace">
      <text x="0" y="10"  class="text-green" font-weight="bold">TOTAL STARS:<tspan x="148" class="text-white" font-weight="normal">{stars}</tspan></text>
      <text x="0" y="32"  class="text-green" font-weight="bold">TOTAL COMMITS:<tspan x="148" class="text-white" font-weight="normal">{commits}</tspan></text>
      <text x="0" y="54"  class="text-green" font-weight="bold">PULL REQUESTS:<tspan x="148" class="text-white" font-weight="normal">{prs}</tspan></text>
      <text x="0" y="76"  class="text-green" font-weight="bold">TOTAL ISSUES:<tspan x="148" class="text-white" font-weight="normal">{issues}</tspan></text>
      <text x="0" y="98"  class="text-green" font-weight="bold">CONTRIBUTED TO:<tspan x="148" class="text-white" font-weight="normal">{contribs}</tspan></text>
      <text x="0" y="120" class="text-green" font-weight="bold">YEARS ACTIVE:<tspan x="148" class="text-white" font-weight="normal">{joined}</tspan></text>
    </g>
    <g transform="translate(308,100)">
      <circle cx="0" cy="0" r="34" fill="none" stroke="{COLORS['gold']}" stroke-width="4" opacity="0.2"/>
      <circle cx="0" cy="0" r="34" fill="none" stroke="{COLORS['gold']}" stroke-width="4" stroke-dasharray="200" stroke-dashoffset="50" stroke-linecap="round"/>
      <text x="0" y="8"  class="monospace text-gold" font-size="20" text-anchor="middle" font-weight="bold">{rank}</text>
      <text x="0" y="48" class="monospace text-gold" font-size="8"  text-anchor="middle">RANK</text>
    </g>
  </g>

  <rect x="400" y="42" width="383" height="200" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
  <g transform="translate(400,42)">
    <text x="20" y="22" class="monospace text-gold" font-size="12" font-weight="bold">[ COMMITS - THIS YEAR ]</text>
    <defs>
      <linearGradient id="chart-grad-ly" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{COLORS['green']}" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="{COLORS['green']}" stop-opacity="0.0"/>
      </linearGradient>
    </defs>
    <svg x="18" y="30" width="{G1_W}" height="155" viewBox="0 0 {G1_W} 155" preserveAspectRatio="none">
      <line x1="0" y1="{int(G1_H*0.33)}" x2="{G1_W}" y2="{int(G1_H*0.33)}" stroke="{COLORS['green']}" stroke-width="0.5" opacity="0.08" stroke-dasharray="2 2"/>
      <line x1="0" y1="{int(G1_H*0.66)}" x2="{G1_W}" y2="{int(G1_H*0.66)}" stroke="{COLORS['green']}" stroke-width="0.5" opacity="0.08" stroke-dasharray="2 2"/>
      {g1_months_xml}
      <path d="{g1_fill}" fill="url(#chart-grad-ly)" stroke="none" class="chart-fill"/>
      <path d="{g1_stroke}" fill="none" stroke="{COLORS['green']}" stroke-width="2" class="chart-line-g1"/>
    </svg>
  </g>

  <!-- ═══ ROW 2: Languages (left) + Top Repositories (right) ═══ -->
  <rect x="15" y="254" width="375" height="160" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
  <g transform="translate(15,254)">
    <text x="20" y="22" class="monospace text-gold" font-size="12" font-weight="bold">[ MOST USED LANGUAGES ]</text>
    {langs_xml}
  </g>

  <rect x="400" y="254" width="383" height="160" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
  <g transform="translate(400,254)">
    <text x="20" y="22" class="monospace text-gold" font-size="12" font-weight="bold">[ TOP REPOSITORIES ]</text>
    {repos_xml}
  </g>

  <!-- ═══ ROW 3: All-Time Graph (full width) ═══ -->
  <rect x="15" y="426" width="770" height="207" fill="none" stroke="{COLORS['green']}" stroke-width="2"/>
  <g transform="translate(15,426)">
    <text x="20" y="22" class="monospace text-gold" font-size="12" font-weight="bold">[ ALL-TIME CONTRIBUTION GRAPH ]</text>
    <defs>
      <linearGradient id="chart-grad-at" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{COLORS['green']}" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="{COLORS['green']}" stop-opacity="0.0"/>
      </linearGradient>
    </defs>
    <svg x="15" y="30" width="{G2_W}" height="165" viewBox="0 0 {G2_W} 165" preserveAspectRatio="none">
      <line x1="0" y1="{int(G2_H*0.33)}" x2="{G2_W}" y2="{int(G2_H*0.33)}" stroke="{COLORS['green']}" stroke-width="0.5" opacity="0.08" stroke-dasharray="2 2"/>
      <line x1="0" y1="{int(G2_H*0.66)}" x2="{G2_W}" y2="{int(G2_H*0.66)}" stroke="{COLORS['green']}" stroke-width="0.5" opacity="0.08" stroke-dasharray="2 2"/>
      {g2_years_xml}
      <path d="{g2_fill}" fill="url(#chart-grad-at)" stroke="none" class="chart-fill"/>
      <path d="{g2_stroke}" fill="none" stroke="{COLORS['green']}" stroke-width="2" class="chart-line-g2"/>
    </svg>
  </g>"""


def generate_dashboard_svg(header_elems, stack_elems, metrics_elems):
    h_height = CONFIG["layout"]["header_height"]
    s_height = CONFIG["layout"]["stack_height"]
    m_height = CONFIG["layout"]["metrics_height"]
    total_height = h_height + s_height + m_height

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{total_height}" viewBox="0 0 800 {total_height}">
  <defs>
    <pattern id="bg-grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="{COLORS['green']}" stroke-width="0.5" opacity="{GRID_OPACITY}" />
    </pattern>
  </defs>
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-green {{ fill: {COLORS['green']}; }}
    .text-green-dim {{ fill: {COLORS['green']}; opacity: 0.65; }}
    .text-gold {{ fill: {COLORS['gold']}; }}
    .text-white {{ fill: {COLORS['white']}; }}
    .text-red {{ fill: {COLORS['red']}; }}
    @keyframes badgeFadeIn {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    .badge-anim {{
      animation: badgeFadeIn 0.4s ease-out forwards;
      opacity: 0;
    }}
    @keyframes spinGlobe3D {{
      from {{ transform: rotateX(20deg) rotateY(0deg); }}
      to {{ transform: rotateX(20deg) rotateY(360deg); }}
    }}
    @keyframes fadeOut {{
      0%, 99% {{ opacity: 1; visibility: visible; }}
      100% {{ opacity: 0; visibility: hidden; }}
    }}
    @keyframes flashStep {{
      0%, 100% {{ opacity: 0; visibility: hidden; }}
      1%, 99% {{ opacity: 1; visibility: visible; }}
    }}
    @keyframes fadeInPersistent {{
      0% {{ opacity: 0; visibility: hidden; }}
      100% {{ opacity: 1; visibility: visible; }}
    }}
    @keyframes blinkDot {{
      0%, 100% {{ opacity: 0.2; }}
      50% {{ opacity: 0.9; }}
    }}
    @keyframes fadeOutCell {{
      0% {{ opacity: 1; }}
      100% {{ opacity: 0; }}
    }}
    @keyframes drawPath {{
      from {{ stroke-dashoffset: 6000; }}
      to {{ stroke-dashoffset: 0; }}
    }}
    @keyframes fadeInFill {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    .chart-line-g1 {{
      stroke-dasharray: 6000;
      stroke-dashoffset: 6000;
      animation: drawPath 2.5s ease-out forwards;
      animation-delay: 1.5s;
    }}
    .chart-line-g2 {{
      stroke-dasharray: 6000;
      stroke-dashoffset: 6000;
      animation: drawPath 4.0s ease-out forwards;
      animation-delay: 1.5s;
    }}
    .chart-fill {{
      opacity: 0;
      animation: fadeInFill 1.5s ease-out forwards;
      animation-delay: 3.5s;
    }}
  </style>

  <!-- Background and Full Borders -->
  <rect x="0" y="0" width="800" height="{total_height}" fill="{COLORS['background']}"/>
  <rect x="0" y="0" width="800" height="{h_height + s_height}" fill="url(#bg-grid)"/>
  <rect x="0" y="0" width="800" height="{total_height}" stroke="{COLORS['green']}" stroke-width="4" fill="none"/>

  <!-- Part 1: Header (0 to {h_height}) -->
  <g transform="translate(0, 0)">
{header_elems}
  </g>

  <!-- Part 2: Stack ({h_height} to {h_height + s_height}) -->
  <g transform="translate(0, {h_height})">
    <line x1="0" y1="0" x2="800" y2="0" stroke="{COLORS['green']}" stroke-width="2"/>
{stack_elems}
  </g>

  <!-- Part 3: Metrics ({h_height + s_height} to {total_height}) -->
  <g transform="translate(0, {h_height + s_height})">
    <line x1="0" y1="0" x2="800" y2="0" stroke="{COLORS['green']}" stroke-width="2"/>
{metrics_elems}
  </g>
</svg>"""

    with open("profile/terminal_dashboard.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated terminal_dashboard.svg")

def main():
    os.makedirs("profile", exist_ok=True)
    
    # 1. Fetch Stack badges
    badges = CONFIG["badges"]
    embeds = []
    for url in badges:
        b64, width = fetch_badge_base64(url)
        embeds.append((b64, width))

    # 2. Get XML elements for segments
    header_elems, top_b64, left_b64, down_b64 = generate_header_xml_elements()
    stack_elems = generate_stack_xml_elements(embeds)
    metrics_elems = generate_metrics_xml_elements()

    # 3. Generate individual standalone files (for compatibility)
    h_height = CONFIG["layout"]["header_height"]
    s_height = CONFIG["layout"]["stack_height"]
    m_height = CONFIG["layout"]["metrics_height"]

    header_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{h_height}" viewBox="0 0 800 {h_height}">
  <defs>
    <pattern id="bg-grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="{COLORS['green']}" stroke-width="0.5" opacity="{GRID_OPACITY}" />
    </pattern>
  </defs>
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-green {{ fill: {COLORS['green']}; }}
    .text-green-dim {{ fill: {COLORS['green']}; opacity: 0.65; }}
    .text-gold {{ fill: {COLORS['gold']}; }}
    .text-white {{ fill: {COLORS['white']}; }}
    .text-red {{ fill: {COLORS['red']}; }}
    @keyframes fadeOut {{
      0%, 99% {{ opacity: 1; visibility: visible; }}
      100% {{ opacity: 0; visibility: hidden; }}
    }}
    @keyframes flashStep {{
      0%, 100% {{ opacity: 0; visibility: hidden; }}
      1%, 99% {{ opacity: 1; visibility: visible; }}
    }}
    @keyframes fadeInPersistent {{
      0% {{ opacity: 0; visibility: hidden; }}
      100% {{ opacity: 1; visibility: visible; }}
    }}
    @keyframes blinkDot {{
      0%, 100% {{ opacity: 0.2; }}
      50% {{ opacity: 0.9; }}
    }}
    @keyframes fadeOutCell {{
      0% {{ opacity: 1; }}
      100% {{ opacity: 0; }}
    }}
  </style>
  <rect x="0" y="0" width="800" height="{h_height}" fill="{COLORS['background']}"/>
  <rect x="0" y="0" width="800" height="{h_height}" fill="url(#bg-grid)"/>
  <path d="M 0,{h_height} L 0,0 L 800,0 L 800,{h_height}" stroke="{COLORS['green']}" stroke-width="4" fill="none"/>
{header_elems}
</svg>"""
    with open("profile/terminal_header.svg", "w", encoding="utf-8") as f:
        f.write(header_svg)

    stack_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{s_height}" viewBox="0 0 800 {s_height}">
  <defs>
    <pattern id="bg-grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="{COLORS['green']}" stroke-width="0.5" opacity="{GRID_OPACITY}" />
    </pattern>
  </defs>
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-green-dim {{ fill: {COLORS['green']}; opacity: 0.65; }}
    .text-gold {{ fill: {COLORS['gold']}; }}
    @keyframes badgeFadeIn {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    .badge-anim {{
      animation: badgeFadeIn 0.4s ease-out forwards;
      opacity: 0;
    }}
    @keyframes spinGlobe3D {{
      from {{ transform: rotateX(20deg) rotateY(0deg); }}
      to {{ transform: rotateX(20deg) rotateY(360deg); }}
    }}
  </style>
  <rect x="0" y="0" width="800" height="{s_height}" fill="{COLORS['background']}"/>
  <rect x="0" y="0" width="800" height="{s_height}" fill="url(#bg-grid)"/>
  <line x1="0" y1="0" x2="0" y2="{s_height}" stroke="{COLORS['green']}" stroke-width="4"/>
  <line x1="800" y1="0" x2="800" y2="{s_height}" stroke="{COLORS['green']}" stroke-width="4"/>
{stack_elems}
</svg>"""
    with open("profile/terminal_stack.svg", "w", encoding="utf-8") as f:
        f.write(stack_svg)

    metrics_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{m_height}" viewBox="0 0 800 {m_height}">
  <defs>
    <pattern id="bg-grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="{COLORS['green']}" stroke-width="0.5" opacity="{GRID_OPACITY}" />
    </pattern>
  </defs>
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-green {{ fill: {COLORS['green']}; }}
    .text-green-dim {{ fill: {COLORS['green']}; opacity: 0.65; }}
    .text-gold {{ fill: {COLORS['gold']}; }}
    .text-white {{ fill: {COLORS['white']}; }}
    @keyframes drawPath {{
      from {{ stroke-dashoffset: 6000; }}
      to {{ stroke-dashoffset: 0; }}
    }}
    @keyframes fadeInFill {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    .chart-line-g1 {{
      stroke-dasharray: 6000;
      stroke-dashoffset: 6000;
      animation: drawPath 2.5s ease-out forwards;
      animation-delay: 1.5s;
    }}
    .chart-line-g2 {{
      stroke-dasharray: 6000;
      stroke-dashoffset: 6000;
      animation: drawPath 4.0s ease-out forwards;
      animation-delay: 1.5s;
    }}
    .chart-fill {{
      opacity: 0;
      animation: fadeInFill 1.5s ease-out forwards;
      animation-delay: 3.5s;
    }}
  </style>
  <rect x="0" y="0" width="800" height="{m_height}" fill="{COLORS['background']}"/>
  <path d="M 0,0 L 0,{m_height} L 800,{m_height} L 800,0" stroke="{COLORS['green']}" stroke-width="4" fill="none"/>
{metrics_elems}
</svg>"""
    with open("profile/terminal_metrics.svg", "w", encoding="utf-8") as f:
        f.write(metrics_svg)

    # 4. Generate the main unified dashboard
    generate_dashboard_svg(header_elems, stack_elems, metrics_elems)

if __name__ == "__main__":
    main()
