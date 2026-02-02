from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Beginner Friendly: Allow everyone

# Connect to MongoDB
client = MongoClient("mongodb+srv://akabesh2000:AKabesh46@devvault.tpcaxtu.mongodb.net/?appName=DevVault")
db = client["devvault"]
users_collection = db["users"]
code_collection = db["code"]

# --- AUTHENTICATION (Keep as is) ---
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if users_collection.find_one({"username": data["username"]}):
        return jsonify({"message": "Exists"}), 400
    users_collection.insert_one(data)
    # Create empty code document for new user immediately
    code_collection.insert_one({
        "username": data["username"], 
        "frontend": [], "backend": [], "database": []
    })
    return jsonify({"message": "Created"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = users_collection.find_one(data)
    if user: return jsonify({"message": "success"}), 200
    return jsonify({"message": "Invalid"}), 401


# --- REST API FOR CODE ---

# 1. GET: Fetch all data for a user
@app.route("/code/<username>", methods=["GET"])
def get_code(username):
    data = code_collection.find_one({"username": username})
    if data:
        # Remove _id so it doesn't break JSON
        data.pop("_id", None)
        return jsonify(data)
    return jsonify({"frontend": [], "backend": [], "database": []})


# 2. POST: Add a NEW file
@app.route("/code/add", methods=["POST"])
def add_file():
    data = request.json
    username = data["username"]
    domain = data["domain"]   # 'frontend', 'backend', or 'database'
    new_file = {"name": data["name"], "content": data["content"]}

    # MongoDB $push: Adds item to array
    code_collection.update_one(
        {"username": username},
        {"$push": {domain: new_file}}
    )
    return jsonify({"message": "File Added"})


# 3. PUT: Update an EXISTING file content
@app.route("/code/update", methods=["PUT"])
def update_file():
    data = request.json
    username = data["username"]
    domain = data["domain"]
    file_name = data["name"]
    new_content = data["content"]

    # MongoDB Update with Array Filter ($)
    # "domain.$.content": Update content where name matches
    code_collection.update_one(
        {"username": username, f"{domain}.name": file_name},
        {"$set": {f"{domain}.$.content": new_content}}
    )
    return jsonify({"message": "File Updated"})


# 4. DELETE: Remove a file
@app.route("/code/delete", methods=["DELETE"])
def delete_file():
    data = request.json
    username = data["username"]
    domain = data["domain"]
    file_name = data["name"]

    # MongoDB $pull: Removes item from array
    code_collection.update_one(
        {"username": username},
        {"$pull": {domain: {"name": file_name}}}
    )
    return jsonify({"message": "File Deleted"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)