TOPIC_LINKS = {
    # Python
    "python_basics": "https://docs.python.org/3/tutorial/index.html",
    "python_datastructures": "https://docs.python.org/3/tutorial/datastructures.html",
    "python_async": "https://docs.python.org/3/library/asyncio.html",
    "python_gil": "https://realpython.com/python-gil/",
    "python_gc": "https://devguide.python.org/internals/garbage-collector/",
    
    # Django
    "django_intro": "https://docs.djangoproject.com/en/stable/intro/",
    "django_models": "https://docs.djangoproject.com/en/stable/topics/db/models/",
    "django_orm": "https://docs.djangoproject.com/en/stable/topics/db/queries/",
    "django_optimization": "https://docs.djangoproject.com/en/stable/topics/db/optimization/",
    "django_drf": "https://www.django-rest-framework.org/",
    
    # Databases
    "sql_joins": "https://www.postgresqltutorial.com/postgresql-tutorial/postgresql-joins/",
    "postgres_indexes": "https://www.postgresql.org/docs/current/indexes.html",
    "acid": "https://habr.com/ru/articles/555920/",
    "redis": "https://redis.io/docs/latest/develop/get-started/",
    
    # DevOps & Tools
    "docker": "https://docs.docker.com/get-started/",
    "git": "https://git-scm.com/book/ru/v2",
    "celery": "https://docs.celeryq.dev/en/stable/getting-started/",
    "microservices": "https://microservices.io/"
}

def get_resources_str() -> str:
    """Формирует строку для вставки в системный промпт."""
    lines = []
    for key, url in TOPIC_LINKS.items():
        lines.append(f"- {key}: {url}")
    return "\n".join(lines)