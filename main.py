"""
main.py
-------
Point d'entrée unique du pipeline tech-news.
Charge les variables d'environnement depuis .env puis lance le flow Prefect.

Usage :
    python main.py
"""

from dotenv import load_dotenv

load_dotenv()  # charge .env dans os.environ (sans écraser les vraies vars d'env)

from flows.news_pipeline_flow import tech_news_pipeline

if __name__ == "__main__":
    tech_news_pipeline()
