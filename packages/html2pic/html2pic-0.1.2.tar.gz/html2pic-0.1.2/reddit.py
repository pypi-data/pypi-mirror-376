from html2pic import Html2Pic

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
    src: url('font-1.ttf') format('truetype');
}

.card {
    font-family: "x", "CustomFont";
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background-color: #1a1b21;
    border-radius: 12px;
    width: 350px;
    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
}

.avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-image: linear-gradient(45deg, #f97794, #623aa2);
}

.user-info {
    display: flex;
    flex-direction: column;
}

h2 {
    margin: 0;
    font-size: 22px;
    font-weight: 600;
    color: #e6edf3;
}

p {
    margin: 0;
    font-size: 16px;
    color: #7d8590;
}
'''

renderer = Html2Pic(html, css)
image = renderer.render()
image.save("profile_card.png")