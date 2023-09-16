from flask import (
    Flask,
    request,
    redirect,
    url_for,
    flash
)
from flask import render_template
from .data_validators import validate_url
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    return render_template('index.html', )


@app.post('/urls')
def add_url():
    input_url = request.form['url']
    is_valid, error_message = validate_url(input_url)
    if not is_valid:
        flash(error_message, 'danger')
        return render_template('index.html',), 422

    else:
        parsed_url = urlparse(input_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        try:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute(
                        'SELECT id FROM urls WHERE name=%s', (base_url,))
                    existing_record = curs.fetchone()
                    if existing_record:
                        url_id = existing_record[0]
                        flash('Страница уже существует', 'info')
                    else:
                        curs.execute(
                            'INSERT INTO urls (name) VALUES (%s)',
                            (base_url,))
                        curs.execute(
                            'SELECT id FROM urls WHERE name=%s',
                            (base_url,))
                        url_id = curs.fetchone()[0]
                        flash('Страница успешно добавлена', 'success')
                    return redirect(url_for('view_url', id=url_id))
        except psycopg2.Error:
            flash('Произошла ошибка при добавлении URL в базу данных. \
                Пожалуйста, попробуйте снова.')


@app.get('/urls')
def show_urls():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute('''
                            SELECT
                                urls.id,
                                name,
                                MAX(url_checks.created_at) AS latest_data,
                                status_code
                            FROM
                                urls
                            LEFT JOIN
                                url_checks
                            ON urls.id = url_checks.url_id
                            GROUP BY
                                urls.id, name, status_code
                            ORDER BY
                                urls.id DESC
                        ''')
            all_records = curs.fetchall()
    return render_template('urls.html', records=all_records)


@app.route('/urls/<int:id>', methods=['GET'])
def view_url(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute('SELECT * FROM urls WHERE id=%s', (id,))
            data_urls = curs.fetchone()
            id = data_urls.id
            name = data_urls.name
            formatted_date = data_urls.created_at.strftime('%Y-%m-%d')
            curs.execute(
                'SELECT * FROM url_checks WHERE url_id=%s order by id DESC',
                (id,))
            all_checks = curs.fetchall()
    return render_template('url_id.html',
                           id=id,
                           name=name,
                           created_at=formatted_date,
                           checks=all_checks,
                           )


def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    h1_tag = soup.find('h1')
    h1_content = h1_tag.text if h1_tag else None

    title_tag = soup.title
    title_text = title_tag.text if title_tag else None

    description_tag = soup.find('meta', attrs={'name': 'description'})
    description_content = description_tag['content'] \
        if description_tag else None

    return h1_content, title_text, description_content


@app.post('/urls/<int:id>/checks')
def check_url(id):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    'SELECT name FROM urls WHERE id=%s', (id,)
                )
                url_name = curs.fetchone()[0]
                response = requests.get(url_name)
                status_code = response.status_code
                error_codes = [400, 401, 403, 404, 422, 429, 500, 502, 503]
                if status_code not in error_codes:
                    h1_content, title_text, description_content = (
                        parse_html(response.content))
                    curs.execute(
                        '''INSERT INTO
                            url_checks (url_id, status_code,
                            h1, title, description)
                        VALUES
                            (%s, %s, %s, %s, %s)''',
                        (id, status_code, h1_content,
                         title_text, description_content)
                    )
                    flash('Страница успешно проверена', 'success')
                else:
                    flash('Произошла ошибка при проверке', 'danger')
    except Exception as err:
        flash(f'Произошла ошибка при проверке: {err}', 'danger')
    return redirect(url_for('view_url', id=id))


if __name__ == "__main__":
    app.run(debug=False)
