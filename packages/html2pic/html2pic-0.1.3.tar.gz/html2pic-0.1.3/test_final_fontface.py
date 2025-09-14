#!/usr/bin/env python3
"""
Final test to validate @font-face functionality is working correctly
"""

from src.html2pic import Html2Pic

# Test 1: Basic @font-face with weight fallback (like reddit.py)
print("=== TEST 1: Weight Fallback ===")
html1 = '''<h1 style="font-weight: 600;">Bold Text</h1>'''
css1 = '''
@font-face {
    font-family: 'TestFont';
    src: url('regular.ttf');
    font-weight: 400;
}

h1 { font-family: "TestFont", Arial; }
'''

renderer1 = Html2Pic(html1, css1)
print(f"Font registry: {len(renderer1.font_registry)} fonts")
print(f"H1 resolution: {renderer1.font_registry.resolve_font_family('TestFont', '600', 'normal')}")
print(f"Warnings: {len(renderer1.get_warnings())}")

# Test 2: Multiple weights
print("\n=== TEST 2: Multiple Weights ===")
html2 = '''
<div>
    <p style="font-weight: 400;">Normal</p>
    <p style="font-weight: 700;">Bold</p>
</div>
'''
css2 = '''
@font-face {
    font-family: 'MultiFont';
    src: url('regular.ttf');
    font-weight: 400;
}

@font-face {
    font-family: 'MultiFont';
    src: url('bold.ttf');
    font-weight: 700;
}

p { font-family: "MultiFont", Arial; }
'''

renderer2 = Html2Pic(html2, css2)
print(f"Font registry: {len(renderer2.font_registry)} fonts")
print(f"Normal resolution: {renderer2.font_registry.resolve_font_family('MultiFont', '400', 'normal')}")
print(f"Bold resolution: {renderer2.font_registry.resolve_font_family('MultiFont', '700', 'normal')}")
print(f"Warnings: {len(renderer2.get_warnings())}")

# Test 3: Reddit.py exact case
print("\n=== TEST 3: Reddit.py Case ===")
reddit_css = '''
@font-face {
    font-family: 'CustomFont';
    src: url('font-1.ttf');
}

.card {
    font-family: "CustomFont";
}

h2 {
    font-weight: 600;
}
'''

renderer3 = Html2Pic('<div class="card"><h2>Test</h2></div>', reddit_css)
print(f"Font registry: {len(renderer3.font_registry)} fonts")

# Check styling of H2 element
styled = renderer3.styled_tree
def find_h2(node):
    if hasattr(node, 'tag') and node.tag == 'h2':
        return node
    for child in node.children:
        result = find_h2(child)
        if result:
            return result
    return None

h2_node = find_h2(styled)
if h2_node:
    font_family = h2_node.computed_styles.get('font-family', '')
    font_weight = h2_node.computed_styles.get('font-weight', '400')
    resolved = renderer3.font_registry.resolve_font_family(font_family, font_weight, 'normal')
    print(f"H2 font-family: {font_family}")
    print(f"H2 font-weight: {font_weight}")
    print(f"H2 resolved to: {resolved}")

print(f"Warnings: {len(renderer3.get_warnings())}")

print("\n=== ALL TESTS COMPLETED ===")