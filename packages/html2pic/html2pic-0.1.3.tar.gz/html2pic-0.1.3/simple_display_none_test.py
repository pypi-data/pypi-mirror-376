from html2pic import Html2Pic

# Simple test to verify display: none works
print("=== Simple display: none test ===")

# Test 1: Element with display: none should not appear
html1 = '''
<div class="container">
    <div class="box1">Visible Box</div>
    <div class="box2">Hidden Box</div>
</div>
'''

css1 = '''
.container {
    background-color: #f0f0f0;
    padding: 20px;
}

.box1 {
    background-color: #4caf50;
    color: white;
    padding: 10px;
    margin: 5px;
}

.box2 {
    background-color: #f44336;
    color: white;
    padding: 10px;
    margin: 5px;
    display: none;
}
'''

renderer1 = Html2Pic(html1, css1)
image1 = renderer1.render()
image1.save("simple_display_none_test.png")
print("Test 1 completed - should show only green box")

# Test 2: Nested elements with display: none
html2 = '''
<div class="parent">
    <div class="child1">Child 1 (visible)</div>
    <div class="hidden-parent">
        <div class="child2">Child 2 (parent hidden)</div>
        <div class="child3">Child 3 (parent hidden)</div>
    </div>
    <div class="child4">Child 4 (visible)</div>
</div>
'''

css2 = '''
.parent {
    background-color: #e0e0e0;
    padding: 15px;
}

.child1, .child4 {
    background-color: #2196f3;
    color: white;
    padding: 8px;
    margin: 4px;
}

.hidden-parent {
    display: none;
}

.child2, .child3 {
    background-color: #ff9800;
    color: white;
    padding: 8px;
    margin: 4px;
}
'''

renderer2 = Html2Pic(html2, css2)
image2 = renderer2.render()
image2.save("nested_display_none_test.png")
print("Test 2 completed - should show only Child 1 and Child 4")

print("All tests completed successfully!")