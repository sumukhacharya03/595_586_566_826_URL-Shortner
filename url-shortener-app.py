import os
import redis
import hashlib
from flask import Flask, request, redirect, jsonify

def create_app():
    app = Flask(__name__)

    # Connect to Redis
    redis_host = os.environ.get('REDIS_HOST', 'redis')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    try:
        redis_client.ping()
        print("✅ Connected to Redis successfully")
    except Exception as e:
        print(f"❌ Redis connection error: {e}")

    def generate_short_url(long_url):
        # Generate a short hash for the URL
        hash_object = hashlib.md5(long_url.encode())
        short_code = hash_object.hexdigest()[:6]  # Use first 6 characters
        return short_code

    @app.route('/')
    def home():
        return "URL Shortener API is running! Use /shorten to create short URLs."

    @app.route('/shorten', methods=['POST'])
    def shorten_url():
        long_url = request.json.get('url')
        if not long_url:
            return jsonify({"error": "URL is required"}), 400

        # Generate short URL
        short_code = generate_short_url(long_url)

        # Store in Redis with 30-day expiration (2592000 seconds)
        redis_client.setex(short_code, 2592000, long_url)

        short_url = f"http://localhost:5000/{short_code}"
        print(f"✅ Stored in Redis: {short_code} -> {long_url}")

        return jsonify({"original_url": long_url, "short_url": short_url})

    @app.route('/<short_code>', methods=['GET'])
    def redirect_to_url(short_code):
        long_url = redis_client.get(short_code)

        if long_url:
            return redirect(long_url)
        else:
            return jsonify({"error": "URL not found"}), 404

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
