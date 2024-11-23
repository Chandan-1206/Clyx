from flask import Flask, jsonify, request
from pymongo import MongoClient
from mlxtend.frequent_patterns import apriori
import pandas as pd
import logging
import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB URI
db = client['influencer_data']  # Updated database name

# Collections
influencers_collection = db['influencers_summary']  # Updated collection name
posts_collection = db['posts']
users_collection = db['users']

logging.basicConfig(level=logging.INFO)

@app.before_request
def log_request_info():
    logging.info('Headers: %s', request.headers)
    logging.info('Body: %s', request.get_data())

@app.route('/')
def home():
    return "Welcome to InfluencerConnect API"

@app.route('/influencers', methods=['GET'])
def get_influencers():
    try:
        influencers = list(influencers_collection.find())
        for influencer in influencers:
            influencer['_id'] = str(influencer['_id'])  # Convert ObjectId to string
        return jsonify(influencers), 200
    except Exception as e:
        logging.error(f"Error fetching influencers: {e}")
        return jsonify({"error": "Failed to fetch influencers"}), 500

@app.route('/add_influencer', methods=['POST'])
def add_influencer():
    if not request.json or not all(key in request.json for key in (
            'username', 'age', 'gender', 'category', 'followers', 
            'followees', 'engagement_rate', 'audience_age_percentage', 
            'audience_gender_ratio', 'audience_regions')):
        return jsonify({"error": "Missing or invalid data"}), 400

    new_influencer = {
        "username": request.json['username'],
        "age": request.json['age'],
        "gender": request.json['gender'],
        "category": request.json['category'],
        "followers": request.json['followers'],
        "followees": request.json['followees'],
        "engagement_rate": request.json['engagement_rate'],
        "audience_age_percentage": request.json['audience_age_percentage'],
        "audience_gender_ratio": request.json['audience_gender_ratio'],
        "audience_regions": request.json["audience_regions"]
    }

    try:
        # Insert into MongoDB
        result = influencers_collection.insert_one(new_influencer)
        new_influencer['_id'] = str(result.inserted_id)  # Add the generated ID to the influencer data
        return jsonify({"message": "Influencer added successfully", "data": new_influencer}), 201
    except Exception as e:
        logging.error(f"Error adding influencer: {e}")
        return jsonify({"error": "Failed to add influencer"}), 500

@app.route('/update_influencer/<influencer_id>', methods=['PUT'])
def update_influencer(influencer_id):
    if not request.json:
        return jsonify({"error": "Missing data"}), 400

    update_data = {key: request.json[key] for key in request.json if key in (
            'username', 'age', 'gender', 'category', 'followers', 
            'followees', 'engagement_rate', 'audience_age_percentage', 
            'audience_gender_ratio', 'audience_regions')}
    
    try:
        result = influencers_collection.update_one({"_id": ObjectId(influencer_id)}, {"$set": update_data})
        if result.matched_count == 0:
            return jsonify({"error": "Influencer not found"}), 404
        return jsonify({"message": "Influencer updated successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating influencer {influencer_id}: {e}")
        return jsonify({"error": "Failed to update influencer"}), 500

@app.route('/delete_influencer/<influencer_id>', methods=['DELETE'])
def delete_influencer(influencer_id):
    try:
        result = influencers_collection.delete_one({"_id": ObjectId(influencer_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Influencer not found"}), 404
        return jsonify({"message": "Influencer deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting influencer {influencer_id}: {e}")
        return jsonify({"error": "Failed to delete influencer"}), 500

@app.route('/add_post', methods=['POST'])
def add_post():
    if not request.json or not all(key in request.json for key in ('influencer_id', 'content', 'sentiment')):
        return jsonify({"error": "Missing or invalid data"}), 400

    new_post = {
        "influencer_id": request.json['influencer_id'],
        "content": request.json['content'],
        "sentiment": request.json['sentiment'],
        "created_at": datetime.datetime.utcnow()  # Store the current time
    }

    try:
        # Insert into MongoDB
        result = posts_collection.insert_one(new_post)
        new_post['_id'] = str(result.inserted_id)
        return jsonify({"message": "Post added successfully", "data": new_post}), 201
    except Exception as e:
        logging.error(f"Error adding post: {e}")
        return jsonify({"error": "Failed to add post"}), 500

@app.route('/posts/<influencer_id>', methods=['GET'])
def get_posts_by_influencer(influencer_id):
    try:
        posts = list(posts_collection.find({"influencer_id": influencer_id}))
        for post in posts:
            post['_id'] = str(post['_id'])
        return jsonify(posts), 200
    except Exception as e:
        logging.error(f"Error fetching posts for influencer {influencer_id}: {e}")
        return jsonify({"error": "Failed to fetch posts"}), 500

@app.route('/add_comment', methods=['POST'])
def add_comment():
    if not request.json or not all(key in request.json for key in ('username', 'comment', 'post_id')):
        return jsonify({"error": "Missing or invalid data"}), 400

    new_comment = {
        "username": request.json['username'],
        "comment": request.json['comment'],
        "post_id": request.json['post_id'],
        "created_at": datetime.datetime.utcnow()
    }

    try:
        # Insert into MongoDB
        result = users_collection.insert_one(new_comment)
        new_comment['_id'] = str(result.inserted_id)
        return jsonify({"message": "Comment added successfully", "data": new_comment}), 201
    except Exception as e:
        logging.error(f"Error adding comment: {e}")
        return jsonify({"error": "Failed to add comment"}), 500

@app.route('/comments/<post_id>', methods=['GET'])
def get_comments_by_post(post_id):
    try:
        comments = list(users_collection.find({"post_id": post_id}))
        for comment in comments:
            comment['_id'] = str(comment['_id'])
        return jsonify(comments), 200
    except Exception as e:
        logging.error(f"Error fetching comments for post {post_id}: {e}")
        return jsonify({"error": "Failed to fetch comments"}), 500

@app.route('/delete_post/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        result = posts_collection.delete_one({"_id": ObjectId(post_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Post not found"}), 404
        return jsonify({"message": "Post deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting post {post_id}: {e}")
        return jsonify({"error": "Failed to delete post"}), 500

@app.route('/delete_comment/<comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    try:
        result = users_collection.delete_one({"_id": ObjectId(comment_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Comment not found"}), 404
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting comment {comment_id}: {e}")
        return jsonify({"error": "Failed to delete comment"}), 500

@app.route('/apriori', methods=['GET'])
def run_apriori():
    try:
        # Fetch influencer data from MongoDB
        influencers = list(influencers_collection.find())
        
        # Check if any influencers were found
        if not influencers:
            return jsonify({"error": "No influencers found in the database"}), 404

        df = pd.DataFrame(influencers)

        # Check if the required columns exist
        if 'followers' not in df.columns or 'engagement_rate' not in df.columns:
            return jsonify({"error": "Required fields are missing in the influencer data"}), 400

        # Calculate mean values for filtering
        mean_followers = df['followers'].mean()
        mean_engagement_rate = df['engagement_rate'].mean()

        # Filter for high engagement and high followers
        high_engagement_followers = df[(df['followers'] > mean_followers) & (df['engagement_rate'] > mean_engagement_rate)]

        # Sort by followers and engagement rate
        top_influencers = high_engagement_followers.sort_values(by=['followers', 'engagement_rate'], ascending=False).head(10)

        # Prepare the response with only the necessary fields (ID, username)
        result = top_influencers[['influencer_id', 'username', 'followers', 'engagement_rate']].to_dict(orient='records')

        # Check if any top influencers were found
        if not result:
            return jsonify({"message": "No top influencers found"}), 200

        return jsonify(result), 200

    except Exception as e:
        logging.error(f"Apriori algorithm error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
        
if __name__ == '__main__':
    app.run(debug=True, port=5002)