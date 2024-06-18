from flask import Flask, request, send_file, render_template, redirect, url_for
from PIL import Image
import os
import io
import requests
from urllib.parse import urlparse, urljoin


app = Flask(__name__)

# Set up your proxy configuration
proxies = {
    'http': 'https://watchchest.com:443'

 }
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/redirection-checker', methods=['GET', 'POST'])
def redirection_checker():
    if request.method == 'POST':
        url = request.form['url']
        try:
            redirects = []
            response = requests.get(url, allow_redirects=False, proxies=proxies)
            while response.is_redirect or response.status_code in (301, 302, 303, 307, 308):
                scheme = urlparse(response.url).scheme
                redirects.append((response.status_code, scheme, response.url))
                location = response.headers['Location']
                full_url = urljoin(response.url, location)
                response = requests.get(full_url, allow_redirects=False, proxies=proxies)
            scheme = urlparse(response.url).scheme
            final_url = (response.status_code, scheme, response.url)
            return render_template('redirection_checker.html', redirects=redirects, final_url=final_url, url=url)
        except requests.RequestException as e:
            error = str(e)
            return render_template('redirection_checker.html', error=error, url=url)
    return render_template('redirection_checker.html')

@app.route('/url-status-checker', methods=['GET', 'POST'])
def url_status_checker():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if file:
                df = pd.read_excel(file)
                statuses = []
                for index, row in df.iterrows():
                    url = row['URL']
                    try:
                        response = requests.head(url, allow_redirects=True, proxies=proxies)
                        final_url = response.url
                        statuses.append((url, response.status_code, final_url))
                    except requests.RequestException:
                        statuses.append((url, 'Error', ''))
                return render_template('url_status_checker.html', statuses=statuses)
        except Exception as e:
            error = str(e)
            return render_template('url_status_checker.html', error=error)
    return render_template('url_status_checker.html')

@app.route('/upload', methods=['GET', 'POST'])
def image_convert():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and file.filename.lower().endswith('.webp'):
        try:
            img = Image.open(file)
            img = img.convert('RGB')
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=95)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg', as_attachment=True, attachment_filename='converted.jpg')
        except Exception as e:
            return str(e), 500
    else:
        return "Unsupported file type", 400


if __name__ == '__main__':
    app.run(debug=True)
