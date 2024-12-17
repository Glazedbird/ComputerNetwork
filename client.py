from flask import Flask, render_template
from threading import Timer

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'secret!'

@app.route('/')
def index():
    return render_template('index.html')

def open_browser():
    import webbrowser
    webbrowser.open('http://localhost:8000')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)