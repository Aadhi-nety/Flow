from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# Mock Vanna AI for demo purposes
class MockVannaAI:
    def generate_sql(self, question):
        # Simple question to SQL mapping for demo
        question_lower = question.lower()
        
        if 'total spend' in question_lower:
            return "SELECT SUM(spend) as total_spend FROM marketing_data"
        elif 'revenue by channel' in question_lower:
            return "SELECT channel, SUM(revenue) as total_revenue FROM marketing_data GROUP BY channel"
        elif 'conversion rate' in question_lower:
            return "SELECT SUM(clicks) as total_clicks, SUM(conversions) as total_conversions, ROUND((SUM(conversions)::float / SUM(clicks) * 100), 2) as conversion_rate FROM marketing_data"
        elif 'roi' in question_lower:
            return "SELECT SUM(spend) as total_spend, SUM(revenue) as total_revenue, ROUND(((SUM(revenue) - SUM(spend)) / SUM(spend) * 100), 2) as roi FROM marketing_data"
        else:
            return "SELECT * FROM marketing_data LIMIT 10"

# Initialize mock Vanna AI
vn = MockVannaAI()

# Sample data for mock responses
sample_data = [
    {"date": "2024-01-01", "spend": 1000, "revenue": 1500, "channel": "Google Ads", "campaign": "Winter Sale", "impressions": 50000, "clicks": 1200, "conversions": 45},
    {"date": "2024-01-02", "spend": 1200, "revenue": 1800, "channel": "Facebook Ads", "campaign": "New Collection", "impressions": 75000, "clicks": 1500, "conversions": 60},
    {"date": "2024-01-03", "spend": 800, "revenue": 1200, "channel": "Email Marketing", "campaign": "Newsletter", "impressions": 25000, "clicks": 450, "conversions": 18},
]

@app.route('/')
def home():
    return jsonify({"message": "Vanna AI API is running", "status": "healthy"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "vanna-ai"})

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '')
        session_id = data.get('session_id', 'default')
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        # Generate SQL using mock Vanna AI
        sql = vn.generate_sql(question)
        
        # Mock database results based on SQL query
        if 'SUM(spend)' in sql and 'GROUP BY' not in sql:
            total_spend = sum(item['spend'] for item in sample_data)
            results = [{"total_spend": total_spend}]
        elif 'SUM(revenue)' in sql and 'GROUP BY channel' in sql:
            revenue_by_channel = {}
            for item in sample_data:
                channel = item['channel']
                revenue_by_channel[channel] = revenue_by_channel.get(channel, 0) + item['revenue']
            results = [{"channel": k, "total_revenue": v} for k, v in revenue_by_channel.items()]
        elif 'conversion_rate' in sql:
            total_clicks = sum(item['clicks'] for item in sample_data)
            total_conversions = sum(item['conversions'] for item in sample_data)
            conversion_rate = round((total_conversions / total_clicks) * 100, 2) if total_clicks > 0 else 0
            results = [{"total_clicks": total_clicks, "total_conversions": total_conversions, "conversion_rate": conversion_rate}]
        elif 'roi' in sql:
            total_spend = sum(item['spend'] for item in sample_data)
            total_revenue = sum(item['revenue'] for item in sample_data)
            roi = round(((total_revenue - total_spend) / total_spend) * 100, 2) if total_spend > 0 else 0
            results = [{"total_spend": total_spend, "total_revenue": total_revenue, "roi": roi}]
        else:
            results = sample_data

        return jsonify({
            "question": question,
            "sql": sql,
            "results": results,
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/train', methods=['POST'])
def train_model():
    try:
        data = request.get_json()
        question = data.get('question')
        sql = data.get('sql')
        
        if question and sql:
            # In a real implementation, you would train the Vanna model here
            return jsonify({"message": "Training data added successfully (mock)"})
        else:
            return jsonify({"error": "Question and SQL are required for training"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', False))


