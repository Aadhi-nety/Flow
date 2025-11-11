from flask import Flask, request, jsonify
from flask_cors import CORS
from vanna.remote import VannaDefault
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Vanna AI
vn = VannaDefault(model='chinook', api_key=os.getenv('VANNA_API_KEY'))

# Database connection
def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "vanna-ai"})

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        question = data.get('question')
        session_id = data.get('session_id', 'default')
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        # Generate SQL using Vanna AI
        sql = vn.generate_sql(question=question)
        
        # Execute the SQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        cursor.close()
        conn.close()
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append(dict(zip(columns, row)))
        
        return jsonify({
            "question": question,
            "sql": sql,
            "results": formatted_results,
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/train', methods=['POST'])
def train_model():
    # You can add training data here
    try:
        data = request.json
        question = data.get('question')
        sql = data.get('sql')
        
        if question and sql:
            vn.train(question=question, sql=sql)
            return jsonify({"message": "Training data added successfully"})
        else:
            return jsonify({"error": "Question and SQL are required for training"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', False))
