from flask import Flask, jsonify, make_response, request
from flask_caching import Cache
import psycopg2
import time
import hashlib
import json 
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'RedisCache', 'CACHE_DEFAULT_TIMEOUT': 100, 'CACHE_REDIS_HOST': 'localhost', 'CACHE_REDIS_PORT': 6379})

# Connect to Postgres
conn = psycopg2.connect(
    dbname="cache_experiment", user="postgres", password="postgres", host="localhost"
)
cursor = conn.cursor()

cache_hits = 0
cache_misses = 0

def update_cache_stats(hit):
    global cache_hits, cache_misses
    if hit:
        cache_hits += 1
    else:
        cache_misses += 1

@app.route("/product/<int:product_id>")
def get_product(product_id):
    start = time.time()
    cursor.execute("SELECT * FROM product WHERE id=%s", (product_id,))
    product = cursor.fetchone()
    latency = time.time() - start
    print(f"DB Latency: {latency:.4f} sec")

    if product:
        return jsonify({"id": product[0], "name": product[1], "price": float(product[2]), "latency": latency})
    
    return jsonify({"error": "Not found"}), 404


@app.route("/object_cache/<int:product_id>")
def get_product_with_cache(product_id):
    start = time.time()
    cache_key = f"product:{product_id}"
    product = cache.get(cache_key)
    if product:
        latency = time.time() - start
        print(f"Cache Hit Latency: {latency:.4f} sec")
        update_cache_stats(True)
        return jsonify({"data": product, "latency": latency, "source": "cache"})
    
    # Cache miss → fetch from DB
    update_cache_stats(False)
    cursor.execute("SELECT * FROM product WHERE id=%s", (product_id,))
    row = cursor.fetchone()
    if row:
        product = {"id": row[0], "name": row[1], "price": float(row[2])}
        cache.set(cache_key, product)
        latency = time.time() - start
        print(f"DB Latency (Cache Miss): {latency:.4f} sec")
        return jsonify({"data": product, "latency": latency, "source": "db"})
    
    return jsonify({"error": "Not found"}), 404


@app.route("/session_cache_cart/<user_id>")
def get_cart(user_id):
    start = time.time()
    cache_key = f"cart:{user_id}"
    cart = cache.get(cache_key)
    if cart:
        latency = time.time() - start
        update_cache_stats(True)
        print(f"Session Cache Hit: {latency:.4f} sec")
        return jsonify({"user": user_id, "cart": cart, "latency": latency, "source": "cache"})
    
    # Simulate DB fetch
    update_cache_stats(False)
    cart = {"items": ["iPhone 16", "iPhone 15"]}
    cache.set(cache_key, cart)
    latency = time.time() - start
    print(f"Session Cache Miss: {latency:.4f} sec")
    return jsonify({"user": user_id, "cart": cart, "latency": latency, "source": "db"})

@app.route("/cache_stats")
def cache_stats():
    return jsonify({"cache_hits": cache_hits, "cache_misses": cache_misses})

def fetch_products():
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    return [{"id": row[0], "name": row[1], "price": float(row[2])} for row in products]

# run url, open inspect tool and chck fulfilled by. do not reload page to see caching in action. instead enter url again.
@app.route("/products/max-age")
def products_max_age():
    products = fetch_products()
    response = make_response(jsonify(products))
    response.headers['cache-control'] = 'max-age=60'
    return response

@app.route("/products/no-store")
def products_no_store():
    products = fetch_products()
    response = make_response(jsonify(products))
    response.headers['cache-control'] = 'no-store'
    return response

@app.route("/products/no-cache")
def products_no_cache():
    client_e_tag = request.headers.get('if-none-match')
    cached_e_tag = cache.get('products_e_tag')

    if client_e_tag and client_e_tag == cached_e_tag:
        response = make_response('', 304)
        return response
    
    products = fetch_products()
    e_tag = hashlib.md5(json.dumps(products).encode()).hexdigest()
    cache.set('products_e_tag', e_tag)
    response = make_response(jsonify(products))
    response.headers["Cache-Control"] = "no-cache"  # must validate before using cached version
    response.headers['ETag'] = e_tag

    return response


@app.route("/products/must-revalidate")
def products_must_revalidate():
    products = fetch_products()
    response = make_response(jsonify(products))
    response.headers["Cache-Control"] = "must-revalidate, max-age=30"
    return response

if __name__ == "__main__":
    app.run(debug=True)
