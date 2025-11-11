cd C:\Users\aadhi\OneDrive\Desktop\Assignment\analytics-app\apps\vanna

# Update app.py to load and use your real JSON data
@'
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load your actual analytics data
def load_analytics_data():
    try:
        # Adjust the path based on your actual file location
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Analytics_Test_Data.json')
        with open(data_path, 'r') as file:
            data = json.load(file)
        print(f"✅ Loaded {len(data)} records from analytics data")
        return data
    except Exception as e:
        print(f"❌ Error loading analytics data: {e}")
        # Fallback sample data structure
        return [
            {"date": "2024-01-01", "spend": 1000, "revenue": 1500, "channel": "Google Ads", "campaign": "Winter Sale"},
            {"date": "2024-01-02", "spend": 1200, "revenue": 1800, "channel": "Facebook Ads", "campaign": "New Collection"}
        ]

# Load the data on startup
analytics_data = load_analytics_data()

@app.route('/')
def home():
    return jsonify({"message": "Vanna AI API is running with REAL data", "status": "healthy", "data_records": len(analytics_data)})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "vanna-ai", "data_source": "real_analytics_data", "records": len(analytics_data)})

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '').lower()
        
        if not question:
            return jsonify({"error": "Question is required"}), 400

        print(f"Processing question: {question}")
        
        # Convert analytics data to DataFrame for easier processing
        df = pd.DataFrame(analytics_data)
        
        # Analyze the question and generate appropriate response based on REAL data
        response = generate_response_from_real_data(question, df)
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({"error": str(e)}), 500

def generate_response_from_real_data(question, df):
    """Generate responses based on actual analytics data"""
    
    # Basic statistics from REAL data
    total_spend = df['spend'].sum() if 'spend' in df.columns else 0
    total_revenue = df['revenue'].sum() if 'revenue' in df.columns else 0
    total_roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0
    
    # Question pattern matching with REAL data analysis
    if 'total spend' in question:
        sql = "SELECT SUM(spend) as total_spend FROM analytics_data"
        results = [{"total_spend": total_spend}]
        message = f"Based on our analytics data, the total spend is ${total_spend:,.2f}"
        
    elif 'revenue' in question and 'channel' in question:
        if 'channel' in df.columns:
            channel_revenue = df.groupby('channel')['revenue'].sum().reset_index()
            results = channel_revenue.to_dict('records')
            sql = "SELECT channel, SUM(revenue) as total_revenue FROM analytics_data GROUP BY channel ORDER BY total_revenue DESC"
            message = "Here's the revenue breakdown by channel from our actual data:"
        else:
            results = [{"message": "Channel data not available in dataset"}]
            sql = "SELECT 'Channel data not available' as status"
            message = "Channel information not found in the analytics data"
            
    elif 'conversion' in question or 'conversion rate' in question:
        # If you have conversion data in your JSON
        if 'conversions' in df.columns and 'clicks' in df.columns:
            total_clicks = df['clicks'].sum()
            total_conversions = df['conversions'].sum()
            conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            results = [{"total_clicks": total_clicks, "total_conversions": total_conversions, "conversion_rate": round(conversion_rate, 2)}]
            sql = "SELECT SUM(clicks) as total_clicks, SUM(conversions) as total_conversions, ROUND((SUM(conversions)::float / SUM(clicks) * 100), 2) as conversion_rate FROM analytics_data"
            message = f"Based on actual data, the conversion rate is {conversion_rate:.2f}%"
        else:
            results = [{"conversion_rate": "Data not available", "note": "Conversion columns not found in dataset"}]
            sql = "SELECT 'Conversion data not available' as status"
            message = "Conversion data not available in the current analytics dataset"
            
    elif 'roi' in question or 'return on investment' in question:
        results = [{"total_spend": total_spend, "total_revenue": total_revenue, "roi": round(total_roi, 2)}]
        sql = "SELECT SUM(spend) as total_spend, SUM(revenue) as total_revenue, ROUND(((SUM(revenue) - SUM(spend)) / SUM(spend) * 100), 2) as roi FROM analytics_data"
        message = f"The overall ROI from our analytics data is {total_roi:.2f}%"
        
    elif 'channel' in question and 'spend' in question:
        if 'channel' in df.columns and 'spend' in df.columns:
            channel_spend = df.groupby('channel')['spend'].sum().reset_index()
            results = channel_spend.to_dict('records')
            sql = "SELECT channel, SUM(spend) as total_spend FROM analytics_data GROUP BY channel ORDER BY total_spend DESC"
            message = "Here's the spend breakdown by channel from our actual data:"
        else:
            results = [{"message": "Required columns not available"}]
            sql = "SELECT 'Data not available' as status"
            message = "Required data columns not found in analytics dataset"
            
    elif 'average' in question and 'spend' in question:
        avg_spend = df['spend'].mean() if 'spend' in df.columns else 0
        results = [{"average_spend": round(avg_spend, 2)}]
        sql = "SELECT AVG(spend) as average_spend FROM analytics_data"
        message = f"The average spend from our analytics data is ${avg_spend:,.2f}"
        
    elif 'top' in question and 'campaign' in question:
        if 'campaign' in df.columns and 'spend' in df.columns:
            top_campaigns = df.groupby('campaign')['spend'].sum().nlargest(5).reset_index()
            results = top_campaigns.to_dict('records')
            sql = "SELECT campaign, SUM(spend) as total_spend FROM analytics_data GROUP BY campaign ORDER BY total_spend DESC LIMIT 5"
            message = "Here are the top 5 campaigns by spend from our actual data:"
        else:
            results = [{"message": "Campaign data not available"}]
            sql = "SELECT 'Campaign data not available' as status"
            message = "Campaign information not found in analytics data"
            
    else:
        # Default response with sample of actual data
        sample_data = df.head(5).to_dict('records')
        results = sample_data
        sql = "SELECT * FROM analytics_data LIMIT 5"
        message = "Here's a sample of our actual analytics data:"

    return {
        "question": question,
        "sql": sql,
        "results": results,
        "message": message,
        "session_id": "real-data-session",
        "data_source": "Analytics_Test_Data.json",
        "records_analyzed": len(df)
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
'@ | Out-File -FilePath app.py -Encoding utf8
# Initialize mock Vanna 



