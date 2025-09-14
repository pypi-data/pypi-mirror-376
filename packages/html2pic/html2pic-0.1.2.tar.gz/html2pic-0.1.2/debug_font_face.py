#!/usr/bin/env python3
"""
Debug script for @font-face parsing
"""

from src.html2pic.css_parser import CssParser

def debug_font_face_parsing():
    css = '''
    @font-face {
        font-family: "TestFont";
        src: url("test.ttf");
        font-weight: bold;
    }

    .test {
        color: red;
    }
    '''

    parser = CssParser()

    print("Starting CSS parsing...")
    rules, font_registry = parser.parse(css)

    print(f"CSS Rules found: {len(rules)}")
    for rule in rules:
        print(f"  - Selector: {rule.selector}, Declarations: {rule.declarations}")

    print(f"Font registry entries: {len(font_registry)}")
    for font_face in font_registry.font_faces:
        print(f"  - Family: {font_face.family}, Src: {font_face.src}, Weight: {font_face.weight}")

if __name__ == "__main__":
    debug_font_face_parsing()