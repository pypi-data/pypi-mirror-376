from html2pic import Html2Pic

# Test individual border-radius properties
html = '''
<div class="container">
    <div class="card-1">
        <h3>Shorthand border-radius</h3>
        <p>border-radius: 15px</p>
    </div>
    <div class="card-2">
        <h3>Individual corners</h3>
        <p>Each corner different</p>
    </div>
    <div class="card-3">
        <h3>Mixed values</h3>
        <p>px and % values</p>
    </div>
</div>
'''

css = '''
.container {
    display: flex;
    gap: 20px;
    padding: 20px;
    background-color: #f0f0f0;
}

.card-1 {
    width: 200px;
    height: 120px;
    background-color: rgba(255, 0, 0, 0.5);
    padding: 15px;
    border: 2px solid #1976d2;
    /* Traditional shorthand border-radius */
    border-radius: 15px;
}

.card-2 {
    width: 200px;
    height: 120px;
    background-color: #f3e5f5;
    padding: 15px;
    border: 2px solid #7b1fa2;
    /* Individual corner border-radius properties */
    border-top-left-radius: 5px;
    border-top-right-radius: 15px;
    border-bottom-right-radius: 25px;
    border-bottom-left-radius: 10px;
}

.card-3 {
    width: 200px;
    height: 120px;
    background-color: #e8f5e8;
    padding: 15px;
    border: 2px solid #388e3c;
    /* Mixed px and % values */
    border-top-left-radius: 20px;
    border-top-right-radius: 50%;
    border-bottom-right-radius: 10px;
    border-bottom-left-radius: 25%;
}

h3 {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: bold;
    color: #333;
}

p {
    margin: 0;
    font-size: 12px;
    color: #666;
}
'''

print("Testing individual border-radius properties...")

try:
    renderer = Html2Pic(html, css)

    # Check if there are any warnings
    warnings = renderer.get_warnings()
    if warnings:
        print("Warnings found:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("No warnings!")

    # Render the image
    image = renderer.render()
    image.save("border_radius_test.png")
    print("SUCCESS: Test image saved as 'border_radius_test.png'")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()