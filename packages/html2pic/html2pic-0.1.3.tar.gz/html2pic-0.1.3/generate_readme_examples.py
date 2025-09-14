from html2pic import Html2Pic

print("Generating README example images...")

# 1. Individual Border-Radius Properties Example
html1 = '''
<div class="card-container">
    <div class="rounded-card">Individual Corner Radii</div>
</div>
'''

css1 = '''
.card-container {
    padding: 20px;
    background-color: #f5f5f5;
}

.rounded-card {
    width: 300px;
    height: 150px;
    background-color: #e1f5fe;
    padding: 20px;
    border: 3px solid #0277bd;

    /* Individual corner border-radius properties */
    border-top-left-radius: 5px;
    border-top-right-radius: 20px;
    border-bottom-right-radius: 40px;
    border-bottom-left-radius: 10px;

    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: #01579b;
}
'''

renderer1 = Html2Pic(html1, css1)
image1 = renderer1.render()
image1.save("border_radius_example.png")
print("SUCCESS: Generated border_radius_example.png")

# 2. Alpha Channel Colors and Display None Example
html2 = '''
<div class="container">
    <div class="visible-card">Visible Card</div>
    <div class="hidden-card">This won't appear</div>
    <div class="transparent-card">Semi-transparent Card</div>
</div>
'''

css2 = '''
.container {
    display: flex;
    flex-direction: column;
    gap: 15px;
    padding: 20px;
}

.visible-card {
    background-color: rgba(76, 175, 80, 0.9);
    padding: 15px;
    border-radius: 8px;
    color: white;
}

.hidden-card {
    background-color: red;
    padding: 15px;
    display: none; /* This element won't be rendered at all */
}

.transparent-card {
    background-color: rgba(33, 150, 243, 0.3); /* Semi-transparent blue */
    padding: 15px;
    border-radius: 8px;
    border: 2px solid rgba(33, 150, 243, 0.8);
}
'''

renderer2 = Html2Pic(html2, css2)
image2 = renderer2.render()
image2.save("advanced_styling_example.png")
print("SUCCESS: Generated advanced_styling_example.png")

print("All README example images generated successfully!")