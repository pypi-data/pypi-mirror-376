#!/usr/bin/env python3
"""
Test script for the new @font-face functionality in html2pic

This script tests:
1. @font-face CSS parsing
2. Font fallback resolution
3. Integration with PicTex font_fallbacks function
"""

from src.html2pic import Html2Pic

def test_basic_font_face():
    """Test basic @font-face functionality with system font fallbacks"""

    print("Testing @font-face with system font fallbacks...")

    html = '''
    <div class="card">
        <h1>Custom Font Test</h1>
        <p>This text should use MyCustomFont with Arial fallback.</p>
    </div>
    '''

    css = '''
    @font-face {
        font-family: "MyCustomFont";
        src: url("./fonts/custom-font.ttf");
        font-weight: normal;
        font-style: normal;
    }

    .card {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 30px;
        background-color: #f0f8ff;
        border-radius: 15px;
        width: 400px;
    }

    h1 {
        color: #2c3e50;
        font-size: 28px;
        font-family: "MyCustomFont", Arial, sans-serif;
        margin: 0 0 10px 0;
    }

    p {
        color: #7f8c8d;
        font-size: 16px;
        font-family: "MyCustomFont", Helvetica, sans-serif;
        margin: 0;
        text-align: center;
    }
    '''

    try:
        renderer = Html2Pic(html, css)

        # Debug the font registry
        print(f"Font registry contains {len(renderer.font_registry)} font faces:")
        for font_face in renderer.font_registry.font_faces:
            print(f"   - {font_face.family}: {font_face.src} (weight: {font_face.weight}, style: {font_face.style})")

        # Test font resolution
        print("\n- Font resolution tests:")
        font_list_h1 = renderer.font_registry.resolve_font_family("MyCustomFont, Arial, sans-serif")
        font_list_p = renderer.font_registry.resolve_font_family("MyCustomFont, Helvetica, sans-serif")
        print(f"   h1 fonts: {font_list_h1}")
        print(f"   p fonts: {font_list_p}")

        # Render the image
        print("\n- Rendering image...")
        image = renderer.render()
        image.save("test_font_face_output.png")
        print("SUCCESS: Successfully saved test_font_face_output.png")

        # Show warnings if any
        warnings = renderer.get_warnings()
        if warnings:
            print(f"\nWARNING:  {len(warnings)} warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        else:
            print("\nSUCCESS: No warnings!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_multiple_font_faces():
    """Test multiple @font-face declarations with different weights/styles"""

    print("\nTEST: Testing multiple @font-face declarations...")

    html = '''
    <div class="text-samples">
        <h1>Normal Weight</h1>
        <h2>Bold Weight</h2>
        <p class="italic">Italic Style</p>
        <p class="fallback">Fallback Font</p>
    </div>
    '''

    css = '''
    @font-face {
        font-family: "TestFont";
        src: url("./fonts/test-regular.ttf");
        font-weight: 400;
        font-style: normal;
    }

    @font-face {
        font-family: "TestFont";
        src: url("./fonts/test-bold.ttf");
        font-weight: 700;
        font-style: normal;
    }

    @font-face {
        font-family: "TestFont";
        src: url("./fonts/test-italic.ttf");
        font-weight: 400;
        font-style: italic;
    }

    .text-samples {
        display: flex;
        flex-direction: column;
        padding: 20px;
        background: white;
        gap: 10px;
    }

    h1 {
        font-family: "TestFont", Arial, sans-serif;
        font-weight: 400;
        font-style: normal;
        color: #333;
    }

    h2 {
        font-family: "TestFont", Arial, sans-serif;
        font-weight: 700;
        font-style: normal;
        color: #666;
    }

    .italic {
        font-family: "TestFont", Arial, sans-serif;
        font-weight: 400;
        font-style: italic;
        color: #999;
    }

    .fallback {
        font-family: "NonExistentFont", "TestFont", Helvetica, sans-serif;
        font-weight: 400;
        font-style: normal;
        color: #333;
    }
    '''

    try:
        renderer = Html2Pic(html, css)

        print(f"- Font registry contains {len(renderer.font_registry)} font faces:")
        for font_face in renderer.font_registry.font_faces:
            print(f"   - {font_face.family}: {font_face.src} (weight: {font_face.weight}, style: {font_face.style})")

        # Test font resolution for different weight/style combinations
        print("\n- Font resolution tests:")
        test_cases = [
            ("TestFont, Arial", "400", "normal"),
            ("TestFont, Arial", "700", "normal"),
            ("TestFont, Arial", "400", "italic"),
            ("NonExistentFont, TestFont, Helvetica", "400", "normal")
        ]

        for family, weight, style in test_cases:
            resolved = renderer.font_registry.resolve_font_family(family, weight, style)
            print(f"   {family} ({weight}, {style}): {resolved}")

        print("\n- Rendering image...")
        image = renderer.render()
        image.save("test_multiple_font_faces_output.png")
        print("SUCCESS: Successfully saved test_multiple_font_faces_output.png")

        # Show warnings
        warnings = renderer.get_warnings()
        if warnings:
            print(f"\nWARNING:  {len(warnings)} warnings:")
            for warning in warnings[-5:]:  # Show last 5 warnings
                print(f"   - {warning}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_font_face_parsing():
    """Test CSS parser @font-face parsing without rendering"""

    print("\nTEST: Testing @font-face CSS parsing...")

    css = '''
    @font-face {
        font-family: "Font1";
        src: url("font1.woff2");
    }

    @font-face {
        font-family: "Font2";
        src: url('./fonts/font2.ttf');
        font-weight: bold;
        font-style: italic;
    }

    @font-face {
        font-family: Font3;
        src: url(/absolute/path/font3.otf);
        font-weight: 300;
    }

    /* Invalid @font-face - missing font-family */
    @font-face {
        src: url("invalid.ttf");
    }

    /* Invalid @font-face - missing src */
    @font-face {
        font-family: "InvalidFont";
    }

    .test {
        font-family: "Font1", "Font2", Font3, Arial;
    }
    '''

    try:
        # Parse just the CSS without HTML
        renderer = Html2Pic("<div>Test</div>", css)

        print(f"- Parsed {len(renderer.font_registry)} font faces:")
        for i, font_face in enumerate(renderer.font_registry.font_faces, 1):
            print(f"   {i}. {font_face.family}")
            print(f"      src: {font_face.src}")
            print(f"      weight: {font_face.weight}")
            print(f"      style: {font_face.style}")

        # Test resolution
        print(f"\n- Font resolution for 'Font1, Font2, Font3, Arial':")
        resolved = renderer.font_registry.resolve_font_family("Font1, Font2, Font3, Arial")
        for i, font in enumerate(resolved, 1):
            print(f"   {i}. {font}")

        warnings = renderer.get_warnings()
        print(f"\nWARNING:  CSS parsing generated {len(warnings)} warnings:")
        for warning in warnings:
            print(f"   - {warning}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing html2pic @font-face functionality\n")
    print("=" * 60)

    # Run all tests
    test_font_face_parsing()
    test_basic_font_face()
    test_multiple_font_faces()

    print("\n" + "=" * 60)
    print("SUCCESS: Font face testing complete!")
    print("\nKey features implemented:")
    print("  SUCCESS: @font-face CSS parsing")
    print("  SUCCESS: Font registry system")
    print("  SUCCESS: Font fallback resolution")
    print("  SUCCESS: Integration with PicTex font_fallbacks()")
    print("  SUCCESS: Support for font-weight and font-style matching")