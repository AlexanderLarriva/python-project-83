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
@app.route('/urls', methods=['GET', 'POST'])
def add_url():
    # messages = get_flashed_messages(with_categories=True)
    if request.method == 'POST':
        input_url = request.form['url']
        # print(url)
        is_valid, error_message = validate_url(input_url)
        if not is_valid:
            flash(error_message, 'danger')
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
    else:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    'SELECT * FROM urls')
                all_records = curs.fetchall()
        return render_template('urls.html', records=all_records)
    return render_template('index.html', )


@app.route('/urls/<int:id>', methods=['GET'])
def view_url(id):
    # messages = get_flashed_messages(with_categories=True)
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            # Получаем ID только что добавленного URL
            curs.execute('SELECT * FROM urls WHERE id=%s', (id,))
            data = curs.fetchone()
            # print(data)
            # if not data:
            # Ситуация, когда записи с таким ID нет
            #     return "Record not found", 404
            id = data.id
            name = data.name
            formatted_date = data.created_at.strftime('%Y-%m-%d')
    return render_template('url_id.html',
                           id=id,
                           name=name,
                           created_at=formatted_date,)


if __name__ == "__main__":
    app.run(debug=False)
