# Utilise une image Python slim officielle
FROM python:3.10-slim

# Installer Chromium et chromedriver (navigateur + driver)
RUN apt-get update && apt-get install -y chromium chromium-chromedriver

# Définir le répertoire de travail dans le container
WORKDIR /app

# Copier les fichiers de ton projet dans le container
COPY . /app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Variables d'environnement (tu peux aussi les définir dans Render)
ENV TELEGRAM_BOT_TOKEN=ton_token_ici
ENV TELEGRAM_CHAT_ID=ton_chat_id_ici
ENV APOGEE=24010503
ENV BIRTHDATE=31/08/1995

# Commande pour démarrer le bot
CMD ["python", "bot.py"]
