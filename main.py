from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import re
import os
from io import BytesIO

app = Flask(__name__)


# Function to fetch valid links
def fetch_valid_links_from_table(url):
    try:
        # Fetch the content of the URL
        response = requests.get(url)
        print(response.text)
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
