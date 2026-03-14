"""
app/extensions.py — Instâncias compartilhadas de extensões Flask.
Importadas aqui para evitar importações circulares.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
