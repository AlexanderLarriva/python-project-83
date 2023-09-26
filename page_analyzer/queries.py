import psycopg2
from psycopg2.extras import NamedTupleCursor
from .url_parser import parse_html
import requests
from .config import DATABASE_URL


def connect_to_db():
    return psycopg2.connect(DATABASE_URL)


def fetch_url_by_name(base_url):
    with connect_to_db() as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id FROM urls WHERE name=%s', (base_url,))
            return curs.fetchone()


def insert_url(base_url):
    with connect_to_db() as conn:
        with conn.cursor() as curs:
            curs.execute('INSERT INTO urls (name) VALUES (%s) RETURNING id',
                         (base_url,))
            return curs.fetchone()[0]


def fetch_all_records():
    query = '''
                SELECT
                    urls.id,
                    name,
                    MAX(url_checks.created_at) AS latest_data,
                    status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id, name, status_code
                ORDER BY urls.id DESC
            '''
    with connect_to_db() as conn:
        with conn.cursor() as curs:
            curs.execute(query)
            return curs.fetchall()


def fetch_data_url(id):
    with connect_to_db() as conn:
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

    return (id, name, formatted_date, all_checks)


def perform_url_check(id):
    with connect_to_db() as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT name FROM urls WHERE id=%s', (id,))
            url_name = curs.fetchone()[0]
            response = requests.get(url_name)
            response.raise_for_status()

            h1_content, title_text, description_content = (
                parse_html(response.content)
            )

            curs.execute(
                '''INSERT INTO
                    url_checks (url_id, status_code, h1, title, description)
                VALUES (%s, %s, %s, %s, %s)''',
                (id, response.status_code, h1_content,
                 title_text, description_content)
            )
