import os
import base64
import urllib.request
import re
import xml.etree.ElementTree as ET

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
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        tree = ET.parse(file_path)
        root = tree.getroot()
        if root.tag.endswith('svg'):
            root.set('x', '660')
            root.set('y', '15')
            root.set('width', '120')
            root.set('height', '20')
            xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
            return re.sub(r'<\?xml[^>]*\?>', '', xml_str)
    except Exception as e:
        print(f"Error parsing system_online.svg: {e}")
    return ""

def get_inline_svg_xml(file_path, x, y, width, height):
    if not os.path.exists(file_path):
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="#111111" stroke="#33cc66" stroke-width="2"/>'
    try:
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        tree = ET.parse(file_path)
        root = tree.getroot()
        if root.tag.endswith('svg'):
            root.set('x', str(x))
            root.set('y', str(y))
            root.set('width', str(width))
            root.set('height', str(height))
            
            # Ensure viewBox exists
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

def generate_header_xml_elements():
    top_b64 = get_base64_image("images/top.jfif")
    left_b64 = get_base64_image("images/left.jpg")
    down_b64 = get_base64_image("images/down.jpg")
    system_online_content = get_system_online_xml()

    return f"""  <!-- Header Bar -->
  <rect x="2" y="2" width="796" height="40" fill="#051a08" stroke="#33cc66" stroke-width="2"/>
  <text x="20" y="26" class="monospace text-green" font-size="14" font-weight="bold">⚠️ WEYLAND-AW CORP</text>
  <text x="400" y="26" class="monospace text-green" font-size="14" font-weight="bold" text-anchor="middle">PLANETS AFFAIRS DATABASE</text>
  <svg x="660" y="15" width="120" height="20" viewBox="0 0 120 20">{system_online_content}</svg>

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

  <!-- Right Column: Biometric Images (More Square Aspect Ratios) -->
  <g transform="translate(460, 60)">
    <!-- Main Photo (Taller / 4:3 Ratio) -->
    <rect x="0" y="0" width="320" height="230" fill="none" stroke="#33cc66" stroke-width="2"/>
    <image href="{top_b64}" x="2" y="2" width="316" height="226" preserveAspectRatio="xMidYMid slice"/>

    <!-- Bottom Left Photo -->
    <rect x="0" y="240" width="155" height="110" fill="none" stroke="#33cc66" stroke-width="2"/>
    <image href="{left_b64}" x="2" y="242" width="151" height="106" preserveAspectRatio="xMidYMid slice"/>

    <!-- Bottom Right Photo -->
    <rect x="165" y="240" width="155" height="110" fill="none" stroke="#33cc66" stroke-width="2"/>
    <image href="{down_b64}" x="167" y="242" width="151" height="106" preserveAspectRatio="xMidYMid slice"/>

    <!-- Caption -->
    <text x="160" y="365" class="monospace text-green" font-size="12" font-weight="bold" text-anchor="middle">SUBJECT BIOMETRIC IMAGES</text>
  </g>""", top_b64, left_b64, down_b64

def generate_stack_xml_elements(embeds):
    elements = """  <!-- Section Header -->
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
        
        elements += f'    <image href="{b64}" x="{x_offset}" y="{y_offset}" width="{w}" height="28" />\n'
        x_offset += w + 8

    elements += "  </g>"
    return elements

def generate_metrics_xml_elements():
    details_xml = get_inline_svg_xml("profile-summary-card-output/chartreuse_dark/0-profile-details.svg", 17, 47, 766, 176)
    stats_xml = get_inline_svg_xml("profile/stats.svg", 17, 247, 451, 191)
    langs_xml = get_inline_svg_xml("profile/languages.svg", 487, 247, 296, 191)

    return f"""  <!-- Section Header -->
  <rect x="2" y="0" width="796" height="30" fill="#051a08" stroke="#33cc66" stroke-width="2"/>
  <text x="20" y="20" class="monospace text-gold" font-size="13" font-weight="bold">[ BIOMETRIC METRICS &amp; PERFORMANCE GRAPH ]</text>

  <!-- Summary Card (Inlined) -->
  <rect x="15" y="45" width="770" height="180" fill="none" stroke="#33cc66" stroke-width="2"/>
  {details_xml}

  <!-- Stats Card (Inlined) -->
  <rect x="15" y="245" width="455" height="195" fill="none" stroke="#33cc66" stroke-width="2"/>
  {stats_xml}

  <!-- Languages Card (Inlined) -->
  <rect x="485" y="245" width="300" height="195" fill="none" stroke="#33cc66" stroke-width="2"/>
  {langs_xml}"""

def generate_dashboard_svg(header_elems, stack_elems, metrics_elems):
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1060" viewBox="0 0 800 1060">
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-green {{ fill: #33cc66; }}
    .text-gold {{ fill: #ffcc00; }}
    .text-white {{ fill: #ffffff; }}
    .text-red {{ fill: #ff5555; }}
  </style>

  <!-- Background and Full Borders -->
  <rect x="0" y="0" width="800" height="1060" fill="#000000"/>
  <rect x="0" y="0" width="800" height="1060" stroke="#33cc66" stroke-width="4" fill="none"/>

  <!-- Part 1: Header (0 to 450) -->
  <g transform="translate(0, 0)">
{header_elems}
  </g>

  <!-- Part 2: Stack (450 to 600) -->
  <g transform="translate(0, 450)">
    <line x1="0" y1="0" x2="800" y2="0" stroke="#33cc66" stroke-width="2"/>
{stack_elems}
  </g>

  <!-- Part 3: Metrics (600 to 1060) -->
  <g transform="translate(0, 600)">
    <line x1="0" y1="0" x2="800" y2="0" stroke="#33cc66" stroke-width="2"/>
{metrics_elems}
  </g>
</svg>"""

    with open("profile/terminal_dashboard.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated terminal_dashboard.svg")

def main():
    os.makedirs("profile", exist_ok=True)
    
    # 1. Fetch Stack badges
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

    # 2. Get XML elements for segments
    header_elems, top_b64, left_b64, down_b64 = generate_header_xml_elements()
    stack_elems = generate_stack_xml_elements(embeds)
    metrics_elems = generate_metrics_xml_elements()

    # 3. Generate individual standalone files (for compatibility)
    header_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-green {{ fill: #33cc66; }}
    .text-gold {{ fill: #ffcc00; }}
    .text-white {{ fill: #ffffff; }}
    .text-red {{ fill: #ff5555; }}
  </style>
  <rect x="0" y="0" width="800" height="450" fill="#000000"/>
  <path d="M 0,450 L 0,0 L 800,0 L 800,450" stroke="#33cc66" stroke-width="4" fill="none"/>
{header_elems}
</svg>"""
    with open("profile/terminal_header.svg", "w", encoding="utf-8") as f:
        f.write(header_svg)

    stack_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="150" viewBox="0 0 800 150">
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-gold {{ fill: #ffcc00; }}
  </style>
  <rect x="0" y="0" width="800" height="150" fill="#000000"/>
  <line x1="0" y1="0" x2="0" y2="150" stroke="#33cc66" stroke-width="4"/>
  <line x1="800" y1="0" x2="800" y2="150" stroke="#33cc66" stroke-width="4"/>
{stack_elems}
</svg>"""
    with open("profile/terminal_stack.svg", "w", encoding="utf-8") as f:
        f.write(stack_svg)

    metrics_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="460" viewBox="0 0 800 460">
  <style>
    .monospace {{ font-family: monospace, Courier, fixed; }}
    .text-gold {{ fill: #ffcc00; }}
  </style>
  <rect x="0" y="0" width="800" height="460" fill="#000000"/>
  <path d="M 0,0 L 0,460 L 800,460 L 800,0" stroke="#33cc66" stroke-width="4" fill="none"/>
{metrics_elems}
</svg>"""
    with open("profile/terminal_metrics.svg", "w", encoding="utf-8") as f:
        f.write(metrics_svg)

    # 4. Generate the main unified dashboard
    generate_dashboard_svg(header_elems, stack_elems, metrics_elems)

if __name__ == "__main__":
    main()
