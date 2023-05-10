from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add')
def add_numbers():
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    z = x + y
    return jsonify({'result': z})

@app.route('/run_script', methods=['POST'])
def run_script():
    param1 = request.form['param1']
    script = 'run_ingestion.sh'
    subprocess.run(["bash", script, param1], check=True)
    return 'Script executed successfully'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
