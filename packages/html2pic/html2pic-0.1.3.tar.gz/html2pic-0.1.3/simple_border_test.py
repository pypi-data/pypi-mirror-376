from html2pic import Html2Pic

# Simple test para verificar que las propiedades individuales funcionan
html = '<div class="test">Individual border-radius test</div>'

css = '''
.test {
    width: 200px;
    height: 100px;
    background-color: lightblue;
    padding: 20px;
    border: 2px solid blue;
    border-top-left-radius: 10px;
    border-top-right-radius: 20px;
    border-bottom-right-radius: 30px;
    border-bottom-left-radius: 5px;
}
'''

renderer = Html2Pic(html, css)
image = renderer.render()
image.save("simple_border_test.png")
print("Simple test completed successfully!")