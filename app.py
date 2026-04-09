from flask import Flask

app = Flask(__name__)

@app.route('/')
@app.route('/<path:path>')
def hello(path=''):
    return "Vercel VIVO! Flask respondeu corretamente."

if __name__ == '__main__':
    app.run(debug=True)
