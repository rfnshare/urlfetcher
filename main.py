from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
import requests
from bs4 import BeautifulSoup
import re
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Function to fetch valid links
def fetch_valid_links_from_table(url):
    # Create a session to maintain login state
    s = requests.Session()
    if 'login_session' in session:
        s.cookies.update(session['login_session'])
    try:
        # Fetch the content of the URL
        response = s.get(url)
        response.raise_for_status()  # Raise an error if the request failed
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return [], str(e)  # Return empty links and the error message

    # Parse the content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Updated regex pattern to match various file types
    file_pattern = re.compile(r'.*\.(mkv|mp4|avi|pdf|txt|zip|rar|doc|docx|ppt|pptx|xls|xlsx|jpg|jpeg|png|gif|csv|json|xml)$')

    links = []

    # Find all <a> tags regardless of their container
    a_tags = soup.find_all('a', href=True)

    for a_tag in a_tags:
        if file_pattern.match(a_tag['href']):
            links.append(a_tag['href'])

    return links, None  # Return the found links and None for no error



# Route to render the UI
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Create a session to maintain login state
    s = requests.Session()
    response = s.post('https://dflix.discoveryftp.net/login/auth', data={
        'username': username,
        'password': password,
        'remember': 'on',
        'loginsubmit': ''
    })

    if response.ok:
        # Parse the response to check for error messages
        soup = BeautifulSoup(response.text, 'html.parser')
        error_message = soup.find('h6', class_='text-danger text-center')

        if error_message:  # Check if there is an error message indicating login failure
            flash('Login failed: ' + error_message.text.strip(), 'error')
            return redirect(url_for('index'))  # Redirect back to index with error message

        # If there's no error, login is successful
        session['login_session'] = s.cookies.get_dict()  # Store session cookies
        flash('Login successful!', 'success')
        return redirect(url_for('index'))  # Redirect to home after successful login
    else:
        flash('Login failed: Unknown error', 'error')  # Handle unexpected errors
        return redirect(url_for('index'))
@app.route('/fetch-links', methods=['GET', 'POST'])
def fetch_links():
    if request.method == 'POST':
        url = request.form.get('url')
        prefix = request.form.get('prefix', '')  # Get prefix, default to empty string if not provided

        links, error = fetch_valid_links_from_table(url)

        # Clear previous data on a new fetch
        if not error and links:
            # Add prefix to each link
            full_links = [f"{prefix}{link}" for link in links]
            return render_template('index.html', links=full_links, prefix=prefix)
        return render_template('index.html', message=error or "No valid links found.")

    # For GET requests, clear the links and prefix to prevent showing old data
    return render_template('index.html', links=[], prefix='')



# Route to download links as a text file
@app.route('/download', methods=['POST'])
def download_links():
    links = request.form.getlist('links')
    prefix = request.form.get('prefix', '')

    if not links:
        return render_template('index.html', message="No valid links to download.")

    # Create text content, using the optional prefix
    text_file_content = "\n".join([f"{prefix}{link}" for link in links])

    # Use an in-memory binary buffer for the file
    buffer = BytesIO()
    buffer.write(text_file_content.encode('utf-8'))
    buffer.seek(0)

    # Send the file for download
    return send_file(
        buffer,
        as_attachment=True,
        download_name="downloaded_links.txt",
        mimetype="text/plain"
    )


if __name__ == '__main__':
    app.run(debug=True)
