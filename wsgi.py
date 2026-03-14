"""
wsgi.py — Entry point da aplicação.
Usado pelo Gunicorn em produção e pelo Flask em desenvolvimento.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
