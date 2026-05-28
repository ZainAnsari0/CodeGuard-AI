from flask import Flask, request, make_response, escape

app = Flask(__name__)

@app.route("/hello")
def hello():
    name = request.args.get("name", "World")
    # SAFE: Using Jinja2 template with autoescaping (Flask default)
    return f"<h1>Hello, {escape(name)}!</h1>"

@app.route("/profile")
def profile():
    user_input = request.args.get("bio", "")
    # SAFE: HTML escaping applied to user input
    from markupsafe import escape as escape_html
    html = f"<div class='bio'>{escape_html(user_input)}</div>"
    return make_response(html)

@app.route("/search")
def search():
    query = request.args.get("q", "")
    # SAFE: Properly escaped user input in template
    return f"""
    <html>
    <body>
        <h2>Search Results for: {escape(query)}</h2>
        <p>No results found.</p>
    </body>
    </html>
    """