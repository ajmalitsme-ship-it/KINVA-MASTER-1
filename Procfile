# ============================================
# PROCFILE - FOR DEPLOYMENT ON RENDER/HEROKU
# ============================================

worker: python bot.py
web: gunicorn --worker-class eventlet -w 1 web:app --bind 0.0.0.0:$PORT
