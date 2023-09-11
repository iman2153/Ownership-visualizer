from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64
import generator  # Assuming megacorp_treemap.py is in the same directory

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    submitted_company = request.form['company']
    img_data = generator.generate_treemap(submitted_company)
    return render_template('index.html', submitted_company=submitted_company, img_data=img_data)

if __name__ == '__main__':
    app.run(debug=True)
