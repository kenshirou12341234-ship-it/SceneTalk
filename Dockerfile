FROM python:3.12-slim

WORKDIR /app

# Node.js/npmをインストール(Tailwind CSSのビルドに必要)
RUN apt-get update -qq && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD sh -c "python manage.py collectstatic --noinput && python manage.py migrate && python manage.py loaddata initial_data.json && gunicorn config.wsgi:application --bind 0.0.0.0:8000"