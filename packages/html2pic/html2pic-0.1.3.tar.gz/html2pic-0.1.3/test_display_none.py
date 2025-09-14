from html2pic import Html2Pic

# Test display: none functionality
html = '''
<div class="container">
    <div class="visible">
        <h3>Visible Element</h3>
        <p>This element should be rendered</p>
    </div>
    <div class="hidden">
        <h3>Hidden Element</h3>
        <p>This element should NOT be rendered (display: none)</p>
    </div>
    <div class="visible">
        <h3>Another Visible Element</h3>
        <p>This element should also be rendered</p>
        <span class="inline-hidden">Hidden inline text</span>
        <span class="inline-visible">Visible inline text</span>
    </div>
</div>
'''

css = '''
.container {
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 20px;
    background-color: #f5f5f5;
    border: 2px solid #333;
}

.visible {
    background-color: #e8f5e8;
    padding: 15px;
    border: 1px solid #4caf50;
    border-radius: 5px;
}

.hidden {
    background-color: #ffebee;
    padding: 15px;
    border: 1px solid #f44336;
    border-radius: 5px;
    /* This entire element should not be rendered */
    display: none;
}

.inline-hidden {
    background-color: #ffcdd2;
    padding: 5px;
    color: red;
    /* This inline element should not be rendered */
    display: none;
}

.inline-visible {
    background-color: #c8e6c9;
    padding: 5px;
    color: green;
}

h3 {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: bold;
    color: #333;
}

p {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #666;
}

span {
    margin-right: 10px;
    font-size: 12px;
}
'''

print("Testing display: none functionality...")

try:
    renderer = Html2Pic(html, css)

    # Check warnings
    warnings = renderer.get_warnings()
    if warnings:
        print("Warnings found:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("No warnings!")

    # Render the image
    image = renderer.render()
    image.save("display_none_test.png")
    print("SUCCESS: Test image saved as 'display_none_test.png'")
    print("Expected result: Only 2 visible green boxes should appear")
    print("The red box and 'Hidden inline text' should be completely absent")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()