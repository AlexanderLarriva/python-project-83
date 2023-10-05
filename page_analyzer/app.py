from flask import (
    Flask,
    request,
    redirect,
    url_for,
    flash
)
from flask import render_template
import requests
from .config import SECRET_KEY
from .data_validators import validate_url
from .url_normalizer import normalize_url
from .url_parser import parse_html
from .queries import (
    fetch_url_by_name,
    insert_url,
    fetch_all_records,
    fetch_data_url,
    fetch_url_name_by_id,
    perform_url_check
)


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def show_homepage():
    return render_template('index.html', )


@app.post('/urls')
def add_url():
    input_url = request.form['url']
    is_valid, error_message = validate_url(input_url)

    if not is_valid:
        flash(error_message, 'danger')
        return render_template('index.html',), 422

    base_url = normalize_url(input_url)
    existing_record = fetch_url_by_name(base_url)

    if existing_record:
        url_id = existing_record[0]
        flash('Страница уже существует', 'info')
    else:
        url_id = insert_url(base_url)
        flash('Страница успешно добавлена', 'success')

    return redirect(url_for('view_url', id=url_id))


@app.get('/urls')
def show_urls():
    all_records = fetch_all_records()
    return render_template('urls.html', records=all_records)


@app.route('/urls/<int:id>', methods=['GET'])
def view_url(id):
    id, name, formatted_date, all_checks = fetch_data_url(id)
    return render_template('url_id.html',
                           id=id,
                           name=name,
                           created_at=formatted_date,
                           checks=all_checks,
                           )


@app.post('/urls/<int:id>/checks')
def check_url(id):
    url_name = fetch_url_name_by_id(id)
    try:
        response = requests.get(url_name)
        response.raise_for_status()
    except requests.HTTPError:
        flash('Произошла ошибка при проверке', 'danger')
    else:
        status_code = response.status_code
        h1_content, title_text, description_content = (
            parse_html(response.content)
        )

        data = {
            "id": id,
            "status_code": status_code,
            "h1_content": h1_content,
            "title_text": title_text,
            "description_content": description_content
        }

        perform_url_check(data)
        flash('Страница успешно проверена', 'success')
    return redirect(url_for('view_url', id=id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
