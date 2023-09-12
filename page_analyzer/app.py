from flask import (
    Flask,
    request,
    redirect,
    url_for,
    flash,
    # get_flashed_messages
)
# подключаем jinja2
from flask import render_template
from .data_validators import validate_url
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv
import requests
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    return render_template('index.html', )


# Добавление инфы о сайте в БД
# и редирект на страницу с инфо о сайте
@app.post('/urls')
def add_url():
    input_url = request.form['url']
    # print(url)
    is_valid, error_message = validate_url(input_url)
    if not is_valid:
        flash(error_message, 'danger')
        return render_template('index.html',)
    else:
        # Нормализуем имя сайта
        parsed_url = urlparse(input_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        try:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute(
                        'SELECT id FROM urls WHERE name=%s', (base_url,))
                    existing_record = curs.fetchone()
                    if existing_record:
                        # Если запись существует
                        url_id = existing_record[0]
                        flash('Страница уже существует', 'info')
                    else:
                        curs.execute(
                            'INSERT INTO urls (name) VALUES (%s)',
                            (base_url,))
                        # Получаем ID только что добавленного URL
                        curs.execute(
                            'SELECT id FROM urls WHERE name=%s',
                            (base_url,))
                        url_id = curs.fetchone()[0]
                        # print(url_id)
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
    # messages = get_flashed_messages(with_categories=True)
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            # Получаем ID только что добавленного URL
            curs.execute('SELECT * FROM urls WHERE id=%s', (id,))
            data_urls = curs.fetchone()
            # print(data)
            # if not data:
            # Ситуация, когда записи с таким ID нет
            #     return "Record not found", 404
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
                error_codes = [400, 401, 403, 404, 429, 500, 502, 503]
                if status_code not in error_codes:
                    curs.execute(
                        '''INSERT INTO
                                url_checks (url_id, status_code)
                        VALUES
                                (%s, %s)''',
                        (id, status_code)
                    )
                    flash('Страница успешно проверена', 'success')
                else:
                    flash('Произошла ошибка при проверке', 'danger')
    except Exception as err:
        flash(f'Произошла ошибка при проверке: {err}', 'danger')
    return redirect(url_for('view_url', id=id))


if __name__ == "__main__":
    app.run(debug=False)
