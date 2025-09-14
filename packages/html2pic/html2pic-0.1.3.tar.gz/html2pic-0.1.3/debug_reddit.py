#!/usr/bin/env python3
"""
Debug script for reddit.py font issue
"""

from src.html2pic import Html2Pic

html = '''
<div class="card">
  <div class="avatar"></div>
  <div class="user-info">
    <h2>pictex_dev</h2>
    <p>@python_renderer</p>
  </div>
</div>
'''

css = '''
@font-face {
    font-family: 'CustomFont';
    src: url('font-1.ttf');
}

.card {
    font-family: "CustomFont";
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background-color: #1a1b21;
    border-radius: 12px;
    width: 350px;
    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
}

h2 {
    margin: 0;
    font-size: 22px;
    font-weight: 600;
    color: #e6edf3;
}
'''

print("=== DEBUGGING FONT RESOLUTION ===")

renderer = Html2Pic(html, css)

print(f"Font registry: {len(renderer.font_registry)} fonts")
for font in renderer.font_registry.font_faces:
    print(f"  - {font.family}: {font.src} (weight: {font.weight}, style: {font.style})")

print(f"\nDOM styling:")
styled_tree = renderer.styled_tree

def print_node_fonts(node, indent=0):
    if hasattr(node, 'computed_styles') and node.computed_styles:
        font_family = node.computed_styles.get('font-family', 'none')
        font_weight = node.computed_styles.get('font-weight', '400')
        font_style = node.computed_styles.get('font-style', 'normal')

        if font_family != 'none':
            print(f"{'  ' * indent}Node ({node.tag}): font-family='{font_family}', weight={font_weight}, style={font_style}")

            # Test resolution
            if renderer.font_registry:
                resolved = renderer.font_registry.resolve_font_family(font_family, font_weight, font_style)
                print(f"{'  ' * indent}  -> Resolved to: {resolved}")

    for child in node.children:
        print_node_fonts(child, indent + 1)

print_node_fonts(styled_tree)

print("\n=== WARNINGS ===")
for warning in renderer.get_warnings():
    print(f"- {warning}")