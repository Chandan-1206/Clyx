from flask import Flask, jsonify, request
from pymongo import MongoClient
from mlxtend.frequent_patterns import apriori
import pandas as pd
import logging
import datetime
from bson.objectid import ObjectId
import getpass
import json

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')  
db = client['clyx']  # Database 

# Collections
brands_collection = db['brands']
influencers_collection = db['influencers']
comments_collection = db['comments_data']
brand_credentials_collection = db['brand_credentials']
influencer_credentials_collection = db['influencer_credentials']

def sign_in():
    email = input("Enter your Email: ")
    password = getpass.getpass("Enter your Password: ")  # Securely take password input

    # Check in the influencers collection
    influencer = influencers_collection.find_one({"email": email, "password": password})  # Ideally, check hashed password
    if influencer:
        print("Sign in successful as Influencer!")
        return influencer  # Return influencer data or token

    # Check in the brands collection
    brand = brands_collection.find_one({"email": email, "password": password})  # Ideally, check hashed password
    if brand:
        print("Sign in successful as Brand!")
        return brand  # Return brand data or token

    print("Invalid email or password.")
    return None

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
            'Name', 'age', 'gender', 'category', 'followers', 
            'followees', 'Engagement_Rate', 'audience_age_percentage', 
            'audience_gender_ratio', 'audience_regions')):
        return jsonify({"error": "Missing or invalid data"}), 400

    new_influencer = {
        "Name": request.json['Name'],
        "age": request.json['age'],
        "gender": request.json['gender'],
        "category": request.json['category'],
        "followers": request.json['followers'],
        "followees": request.json['followees'],
        "Engagement_Rate": request.json['Engagement_Rate'],
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


@app.route('/update_influencer/<Influencer_Id>', methods=['PUT'])
def update_influencer(Influencer_Id):
    if not request.json:
        return jsonify({"error": "Missing data"}), 400

    update_data = {key: request.json[key] for key in request.json if key in (
            'Name', 'age', 'gender', 'category', 'followers', 
            'followees', 'Engagement_Rate', 'audience_age_percentage', 
            'audience_gender_ratio', 'audience_regions')}
    
    try:
        result = influencers_collection.update_one({"_id": ObjectId(Influencer_Id)}, {"$set": update_data})
        if result.matched_count == 0:
            return jsonify({"error": "Influencer not found"}), 404
        return jsonify({"message": "Influencer updated successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating influencer {Influencer_Id}: {e}")
        return jsonify({"error": "Failed to update influencer"}), 500


@app.route('/delete_influencer/<Influencer_Id>', methods=['DELETE'])
def delete_influencer(Influencer_Id):
    try:
        result = influencers_collection.delete_one({"_id": ObjectId(Influencer_Id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Influencer not found"}), 404
        return jsonify({"message": "Influencer deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting influencer {Influencer_Id}: {e}")
        return jsonify({"error": "Failed to delete influencer"}), 500
    


@app.route('/add_comment', methods=['POST'])
def add_comment():
    if not request.json or not all(key in request.json for key in ('Name', 'comment', 'post_id')):
        return jsonify({"error": "Missing or invalid data"}), 400

    new_comment = {
        "Name": request.json['Name'],
        "comment": request.json['comment'],
        "post_id": request.json['post_id'],
        "created_at": datetime.datetime.utcnow()
    }

    try:
        # Insert into MongoDB
        result = comments_collection.insert_one(new_comment)
        new_comment['_id'] = str(result.inserted_id)
        return jsonify({"message": "Comment added successfully", "data": new_comment}), 201
    except Exception as e:
        logging.error(f"Error adding comment: {e}")
        return jsonify({"error": "Failed to add comment"}), 500

@app.route('/comments/<post_id>', methods=['GET'])
def get_comments_by_post(post_id):
    try:
        comments = list(comments_collection.find({"post_id": post_id}))
        for comment in comments:
            comment['_id'] = str(comment['_id'])
        return jsonify(comments), 200
    except Exception as e:
        logging.error(f"Error fetching comments for post {post_id}: {e}")
        return jsonify({"error": "Failed to fetch comments"}), 500


@app.route('/delete_comment/<comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    try:
        result = comments_collection.delete_one({"_id": ObjectId(comment_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Comment not found"}), 404
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting comment {comment_id}: {e}")
        return jsonify({"error": "Failed to delete comment"}), 500

import json  # Make sure to import the json module

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
        result = top_influencers[['Influencer_Id', 'Name', 'Followers', 'Engagement_Rate']].to_dict(orient='records')

        # Format the output
        formatted_result = {
            "total_influencers": len(result),
            "top_influencers": result
        }

        # Return formatted JSON with indentation
        return app.response_class(
            response=json.dumps(formatted_result, indent=4),  # Use indent for pretty printing
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        logging.error(f"Apriori algorithm error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500v


if __name__ == '__main__':
    sign_in()
    app.run(debug=False, port=5003)


