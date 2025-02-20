from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    try:
        port = int(os.environ.get('PORT', 8000))

        # Print server information
        print("\n" + "="*50)
        print("Starting keep-alive server...")
        print(f"Port: {port}")
        print("="*50 + "\n")

        # Ensure we bind to all network interfaces
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Error starting server: {str(e)}")

def keep_alive():
    server_thread = Thread(target=run)
    server_thread.start()
    print("\n" + "="*50)
    print("Keep-alive server started in background thread")
    print("="*50 + "\n")
