from flask import Flask, request, make_response

app = Flask(__name__)

@app.route("/hello")
def hello():
    name = request.args.get("name", "World")
    # VULNERABLE: Reflected XSS - user input directly embedded in HTML without escaping
    return f"<h1>Hello, {name}!</h1>"

@app.route("/profile")
def profile():
    user_input = request.args.get("bio", "")
    # VULNERABLE: Direct HTML injection without sanitization
    html = f"<div class='bio'>{user_input}</div>"
    return make_response(html)

@app.route("/search")
def search():
    query = request.args.get("q", "")
    # VULNERABLE: Reflected XSS in search results
    return f"""
    <html>
    <body>
        <h2>Search Results for: {query}</h2>
        <p>No results found.</p>
    </body>
    </html>
    """