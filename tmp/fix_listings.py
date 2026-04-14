import os

file_path = r'd:\Python Projects\Rentaro\frontend\src\pages\Listings.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                      if (s.lat && s.lon) {
                        const lat = parseFloat(s.lat);
                        const lon = parseFloat(s.lon);
                        setMapCenter([lat, lon]);
                        setMapZoom(16); // High zoom for exact location
                        setViewMode('map');
                        fetchPois(lat, lon);
                      }"""

replacement = """                      if (s.lat && s.lon) {
                        const lat = parseFloat(s.lat);
                        const lon = parseFloat(s.lon);
                        setMapCenter([lat, lon]);
                        setMapZoom(16); // High zoom for exact location
                        if (viewMode === 'map') {
                          fetchPois(lat, lon);
                        }
                      }"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replacement successful")
else:
    print("Target not found exactly. Checking for near matches...")
    # Fallback: simpler search
    if "setViewMode('map');" in content:
        print("Found setViewMode('map');, attempting contextual replacement...")
        # This is risky but let's be specific
        target_v2 = "setMapZoom(16); // High zoom for exact location\n                        setViewMode('map');\n                        fetchPois(lat, lon);"
        if target_v2 in content:
             new_content = content.replace(target_v2, "setMapZoom(16); // High zoom for exact location\n                        if (viewMode === 'map') {\n                          fetchPois(lat, lon);\n                        }")
             with open(file_path, 'w', encoding='utf-8') as f:
                 f.write(new_content)
             print("Replacement V2 successful")
        else:
             print("Target V2 also not found.")
