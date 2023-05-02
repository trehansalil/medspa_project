from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add')
def add_numbers():
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    z = x + y
    return jsonify({'result': z})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
