#!/usr/bin/env python3
"""
Simple Flask test to verify the app can start
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'test',
        'version': '1.0.0'
    })

@app.route('/')
def home():
    return 'Test Flask App Running'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting test Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
