import os
import base64
import urllib.request
import re

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

def get_system_online_xml():
    file_path = "images/system_online.svg"
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'<svg[^>]*>(.*?)</svg>', content, re.DOTALL)
        if match:
            inner_content = match.group(1)
            return f'<svg x="660" y="15" width="120" height="20" viewBox="0 0 120 20">{inner_content}</svg>'
    except Exception as e:
        print(f"Error reading system_online.svg: {e}")
    return ""

def fetch_badge_base64(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            encoded = base64.b64encode(data).decode('utf-8')
            # Extract SVG width from XML (float values allowed)
            svg_text = data.decode('utf-8', errors='ignore')
            width_match = re.search(r'<svg[^>]+width="([^"]+)"', svg_text)
            width = int(float(width_match.group(1))) if width_match else 110
            return f"data:image/svg+xml;base64,{encoded}", width
    except Exception as e:
        print(f"Error fetching badge {url}: {e}")
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", 110

def generate_header_svg():
    top_b64 = get_base64_image("images/top.jfif")
    left_b64 = get_base64_image("images/left.jpg")
    down_b64 = get_base64_image("images/down.jpg")
    system_online_xml = get_system_online_xml()

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="420" viewBox="0 0 800 420">
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-green {{ fill: #33cc66; }}
    .text-gold {{ fill: #ffcc00; }}
    .text-white {{ fill: #ffffff; }}
    .text-red {{ fill: #ff5555; }}
  </style>

  <!-- Background and Top/Left/Right Border -->
  <rect x="0" y="0" width="800" height="420" fill="#000000"/>
  <path d="M 0,420 L 0,0 L 800,0 L 800,420" stroke="#33cc66" stroke-width="4" fill="none"/>

  <!-- Header Bar -->
  <rect x="2" y="2" width="796" height="40" fill="#051a08" stroke="#33cc66" stroke-width="2"/>
  
  <text x="20" y="26" class="monospace text-green" font-size="14" font-weight="bold">⚠️ WEYLAND-AW CORP</text>
  <text x="400" y="26" class="monospace text-green" font-size="14" font-weight="bold" text-anchor="middle">PLANETS AFFAIRS DATABASE</text>
  {system_online_xml}

  <!-- Left Column: Citizen Data (Manually Wrapped Logs) -->
  <g transform="translate(20, 65)">
    <text x="0" y="20" class="monospace text-gold" font-size="18" font-weight="bold">CITIZEN ID: DV4</text>
    <text x="0" y="35" class="monospace text-green" font-size="12">----------------------------------------</text>
    
    <text x="0" y="60" class="monospace text-green" font-size="13" font-weight="bold">NAME: <tspan class="text-white">Rimuwu</tspan> (WARE, WYNDHAM FORREST)</text>
    <text x="0" y="80" class="monospace text-green" font-size="13" font-weight="bold">DEPT: <tspan class="text-red">SALVAGE</tspan> (DEVELOPMENT &amp; DESIGN)</text>
    <text x="0" y="100" class="monospace text-green" font-size="13" font-weight="bold">STATUS: <tspan fill="#55ff55">ACTIVE</tspan></text>
    
    <text x="0" y="130" class="monospace text-green" font-size="13" font-weight="bold">DATE OF BIRTH: <tspan class="text-white">7 FEB 2101</tspan></text>
    <text x="0" y="150" class="monospace text-green" font-size="13" font-weight="bold">BIRTH PLACE: <tspan class="text-white">MARS</tspan></text>
    
    <text x="0" y="190" class="monospace text-gold" font-size="14" font-weight="bold">SYSTEM LOGS / OBJECTIVES:</text>
    
    <!-- Log 1: Japan Enthusiast -->
    <text x="0" y="215" class="monospace text-gold" font-size="12">&gt; <tspan class="text-green">🎌 Japan Enthusiast:</tspan> Passionate about</text>
    <text x="16" y="230" class="monospace text-green" font-size="12">Japanese culture, history, and aesthetics.</text>
    
    <!-- Log 2: Developer Journey -->
    <text x="0" y="255" class="monospace text-gold" font-size="12">&gt; <tspan class="text-green">💻 Developer Journey:</tspan> Started with bots, now building</text>
    <text x="16" y="270" class="monospace text-green" font-size="12">mods, websites, games, &amp; high-load apps.</text>
    
    <!-- Log 3: Current Projects -->
    <text x="0" y="295" class="monospace text-gold" font-size="12">&gt; <tspan class="text-green">🦖 What about now:</tspan> Designing and developing custom</text>
    <text x="16" y="310" class="monospace text-green" font-size="12">independent software systems.</text>
  </g>

  <!-- Right Column: Biometric Images -->
  <g transform="translate(460, 60)">
    <!-- Main Photo -->
    <rect x="0" y="0" width="320" height="180" fill="none" stroke="#33cc66" stroke-width="2"/>
    <image href="{top_b64}" x="2" y="2" width="316" height="176" preserveAspectRatio="xMidYMid slice"/>

    <!-- Bottom Left Photo -->
    <rect x="0" y="190" width="155" height="90" fill="none" stroke="#33cc66" stroke-width="2"/>
    <image href="{left_b64}" x="2" y="192" width="151" height="86" preserveAspectRatio="xMidYMid slice"/>

    <!-- Bottom Right Photo -->
    <rect x="165" y="190" width="155" height="90" fill="none" stroke="#33cc66" stroke-width="2"/>
    <image href="{down_b64}" x="167" y="192" width="151" height="86" preserveAspectRatio="xMidYMid slice"/>

    <!-- Caption -->
    <text x="160" y="305" class="monospace text-green" font-size="12" font-weight="bold" text-anchor="middle">SUBJECT BIOMETRIC IMAGES</text>
  </g>
</svg>"""

    with open("profile/terminal_header.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated terminal_header.svg")

def generate_stack_svg():
    badges = [
        "https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white",
        "https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white",
        "https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white",
        "https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white",
        "https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white",
        "https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black",
        "https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vue.js&logoColor=4FC08D",
        "https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white",
        "https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white",
        "https://img.shields.io/badge/Figma-0ACF83?style=for-the-badge&logo=figma&logoColor=white",
        "https://img.shields.io/badge/GDScript-478CBF?style=for-the-badge&logo=godot-engine&logoColor=white",
        "https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white"
    ]

    embeds = []
    for url in badges:
        b64, width = fetch_badge_base64(url)
        embeds.append((b64, width))

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="150" viewBox="0 0 800 150">
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-gold {{ fill: #ffcc00; }}
  </style>

  <!-- Background and Side Borders -->
  <rect x="0" y="0" width="800" height="150" fill="#000000"/>
  <line x1="0" y1="0" x2="0" y2="150" stroke="#33cc66" stroke-width="4"/>
  <line x1="800" y1="0" x2="800" y2="150" stroke="#33cc66" stroke-width="4"/>

  <!-- Section Header -->
  <rect x="2" y="0" width="796" height="30" fill="#051a08" stroke="#33cc66" stroke-width="2"/>
  <text x="20" y="20" class="monospace text-gold" font-size="13" font-weight="bold">[ ACTIVE MODULES &amp; TOOLKITS ]</text>

  <!-- Badges Grid Layout -->
  <g transform="translate(20, 45)">
"""

    x_offset = 0
    y_offset = 0
    for i, (b64, w) in enumerate(embeds):
        if i > 0 and (i % 6 == 0 or x_offset + w > 760):
            x_offset = 0
            y_offset += 38
        
        svg_content += f'    <image href="{b64}" x="{x_offset}" y="{y_offset}" width="{w}" height="28" />\n'
        x_offset += w + 8

    svg_content += """  </g>
</svg>"""

    with open("profile/terminal_stack.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated terminal_stack.svg")

def generate_metrics_svg():
    details_b64 = get_base64_image("profile-summary-card-output/chartreuse_dark/0-profile-details.svg")
    stats_b64 = get_base64_image("profile/stats.svg")
    langs_b64 = get_base64_image("profile/languages.svg")

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="460" viewBox="0 0 800 460">
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-gold {{ fill: #ffcc00; }}
  </style>

  <!-- Background and Left/Right/Bottom Border -->
  <rect x="0" y="0" width="800" height="460" fill="#000000"/>
  <path d="M 0,0 L 0,460 L 800,460 L 800,0" stroke="#33cc66" stroke-width="4" fill="none"/>

  <!-- Section Header -->
  <rect x="2" y="0" width="796" height="30" fill="#051a08" stroke="#33cc66" stroke-width="2"/>
  <text x="20" y="20" class="monospace text-gold" font-size="13" font-weight="bold">[ BIOMETRIC METRICS &amp; PERFORMANCE GRAPH ]</text>

  <!-- Summary Card -->
  <rect x="15" y="45" width="770" height="180" fill="none" stroke="#33cc66" stroke-width="2"/>
  <image href="{details_b64}" x="17" y="47" width="766" height="176" />

  <!-- Stats Card (Left) -->
  <rect x="15" y="245" width="455" height="195" fill="none" stroke="#33cc66" stroke-width="2"/>
  <image href="{stats_b64}" x="17" y="247" width="451" height="191" />

  <!-- Languages Card (Right) -->
  <rect x="485" y="245" width="300" height="195" fill="none" stroke="#33cc66" stroke-width="2"/>
  <image href="{langs_b64}" x="487" y="247" width="296" height="191" />
</svg>"""

    with open("profile/terminal_metrics.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated terminal_metrics.svg")

if __name__ == "__main__":
    os.makedirs("profile", exist_ok=True)
    generate_header_svg()
    generate_stack_svg()
    generate_metrics_svg()
