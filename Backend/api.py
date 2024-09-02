import os
from flask import Flask, jsonify, request, send_from_directory, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from flask_cors import CORS



app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client["Elib"]
    collection = db["Researches"]
    userCollection = db['Users']

    print("Connected to MongoDB")
except Exception as e:
    print("Error connecting to MongoDB:", e)



UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename , as_attachment=True)
    except FileNotFoundError:
        abort(404, description="File not found")



@app.route('/api/getResearchByDep', methods=['GET'])
def get_researchByDep():

    department = request.args.get('dep')
    print(f'Get request {department}')

    data = list(collection.find({'department': department})) 
    print(f'{data}')
    

    result = [{
        "id": str(d["_id"]), 
        "college": d["college"], 
               "department": d["department"], 
               "title": d["title"], 
               "abstract": d["abstract"], 
                "filename": d['filename'],
               "authors": d["authors"], "approvedDate": d["date_approved"],
                 "filepath": d["filepath"], "researchAdvisers": d["researchAdvisers"],
                 "tags": d["tags"]} 
              for d in data]
    


    if result:
        return jsonify(result)
    else:
        return jsonify({"status": "failed"}), 400




@app.route('/api/getResearchByFilter', methods=['GET'])
def get_researchByFilter():

    filter = request.args.get('fil')
    filVal = request.args.get('val')
    print(f'Get request {filter} & {filVal}')

    data = list(collection.find( {filter: filVal.lower()})) 
    print(f'{data}')
    

    result = [{
        "id": str(d["_id"]), 
        "college": d["college"], 
               "department": d["department"], 
               "title": d["title"], 
               "abstract": d["abstract"], 
               "authors": d["authors"], "approvedDate": d["date_approved"],
               "filename": d['filename'],
                 "filepath": d["filepath"], "researchAdvisers": d["researchAdvisers"],
                 "tags": d["tags"]} 
              for d in data]
    


    if result:
        return jsonify(result)
    else:
        return jsonify({"status": "failed"}), 400


@app.route('/api/research', methods=['POST'])
def add_research():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400
    dat = request.form.get('dat')
    data = json.loads(dat)
    print(data['college'])


    existing_research = collection.find_one(
        {
            "$or": [
                {"title": data['title'].lower()},
                {"filename": data['filename']},
                {"abstract": data['abstract']}
            ]
        }
    )

    
    print(existing_research)
        

    if existing_research:
        return jsonify({
            "status": "failed",
            'message': 'Title, filename, or abstract already exists. Please enter unique values.'
        }), 200

    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'] , data['college'], data['department'] )
    nested_dir = os.path.join(data['college'], data['department'])

    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    nested_dir = str(data['college']) + '/' + str(data['department']) + '/' + str(file.filename)
    file.save(file_path)


    document = {
                    'college': data['college'],
                                    'department': data['department'],
                                "title": data['title'].lower(),
                                "authors":[s.lower() for s in data['authors']],
                                "abstract": data['abstract'],
                                "date_approved": data['approvedDate'][0:10],
                                "filename": data['filename'],
                                "filepath": nested_dir,
                                "researchAdvisers":  [s.lower() for s in data['researhAdvisers']],
                                "tags": [s.lower() for s in data['tags']]
                                }

    
    collection.insert_one(document)
    print(f"Content: {data}")
    print(f"File saved to: {file_path}")


    return jsonify({"status": "success", "filename": file.filename}), 200



@app.route('/api/research', methods=['PATCH'])
def edit_research():
    new_entry = request.get_json()
    if not new_entry:
        return jsonify({"error": "No input data provided"}), 400
    
    document_id = ObjectId(str(new_entry["id"])) 
    print(new_entry)
    

    filter_criteria = {"_id": document_id}  
    update_data = {"$set": new_entry}
    res = collection.update_one(filter_criteria,update_data )

    
    return jsonify({"status": "success"}), 200




@app.route('/api/research', methods=['DELETE'])
def delete_task():
    new_entry = request.get_json()
    if not new_entry:
        return jsonify({"error": "No input data provided"}), 400
    
    document_id = ObjectId(str(new_entry["id"])) 
    print(new_entry)
    

    filter_criteria = {"_id": document_id}  
    result = collection.delete_one(filter_criteria)

    
    
    print(new_entry)

    if result.deleted_count == 1:
        print("Document deleted successfully.")
        return jsonify({"status": "success"}), 200

    else:
        print("Document not found or not deleted.")
        return jsonify({"status": "failed"}), 200










@app.route('/api/register', methods=['POST'])
def register():
    new_entry = request.get_json()
    if not new_entry:
        return jsonify({"error": "No input data provided"}), 400
    

    print(new_entry)
    

    userCollection.insert_one(new_entry)
    
    return jsonify({"status": "success"}), 200


@app.route('/api/login', methods=['POST'])
def login():
    new_entry = request.get_json()
    if not new_entry:
        return jsonify({"error": "No input data provided"}), 400
    

    print(new_entry)
    

    user = userCollection.find_one({'username':new_entry['username'], 'password':new_entry['password']})
    print(user)

    if(user == None):
        return jsonify({"status": "failed"}), 200
    else:
        return jsonify({"status": "success", "user_id": str(user['_id'])}), 200

    

    




if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
