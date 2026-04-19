from flask import Flask
from mx_interpreter import MXLangInterpreter
import time
import threading

app = Flask(__name__)
mx = MXLangInterpreter()

@app.route('/')
def home():
    return "MX Language Bot is Running!"

@app.route('/run')
def run():
    success, message = mx.execute_file('bot.mx')
    return message

def run_bot_forever():
    while True:
        mx.execute_file('bot.mx')
        time.sleep(300)  # Run every 5 minutes

if __name__ == "__main__":
    # Start bot in background
    thread = threading.Thread(target=run_bot_forever)
    thread.daemon = True
    thread.start()
    
    # Run web server
    app.run(host='0.0.0.0', port=10000)
