
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load your REAL analytics data
def load_real_analytics_data():
    try:
        # Path to your real analytics data
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Analytics_Test_Data.json')
        print(f"Loading data from: {data_path}")
        
        with open(data_path, 'r') as file:
            data = json.load(file)
        
        print(f"✅ Successfully loaded {len(data)} records from real analytics data")
        return data
    except Exception as e:
        print(f"❌ Error loading real analytics data: {e}")
        return []

# Load the real data on startup
real_analytics_data = load_real_analytics_data()

@app.route('/')
def home():
    return jsonify({
        "message": "Vanna AI API with REAL Analytics Data", 
        "status": "healthy",
        "data_source": "Analytics_Test_Data.json",
        "records_loaded": len(real_analytics_data)
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "service": "vanna-ai",
        "data_source": "real_analytics_data",
        "records": len(real_analytics_data)
    })

def analyze_real_data(question, data):
    """Analyze real analytics data based on the question"""
    df = pd.DataFrame(data)
    
    # Calculate real statistics from your data
    if 'spend' in df.columns:
        total_spend = df['spend'].sum()
    else:
        # Try to find spend column with different names
        spend_columns = [col for col in df.columns if 'spend' in col.lower() or 'cost' in col.lower()]
        total_spend = df[spend_columns[0]].sum() if spend_columns else 0
    
    if 'revenue' in df.columns:
        total_revenue = df['revenue'].sum()
    else:
        revenue_columns = [col for col in df.columns if 'revenue' in col.lower() or 'income' in col.lower()]
        total_revenue = df[revenue_columns[0]].sum() if revenue_columns else 0
    
    # Question-based analysis of REAL data
    question_lower = question.lower()
    
    if 'total spend' in question_lower:
        sql = "SELECT SUM(spend) as total_spend FROM analytics_data"
        results = [{"total_spend": total_spend}]
        message = f"Based on our real analytics data, the total spend is ${total_spend:,.2f}"
        
    elif 'revenue' in question_lower and 'channel' in question_lower:
        if 'channel' in df.columns and 'revenue' in df.columns:
            channel_revenue = df.groupby('channel')['revenue'].sum().reset_index()
            results = channel_revenue.to_dict('records')
            sql = "SELECT channel, SUM(revenue) as total_revenue FROM analytics_data GROUP BY channel ORDER BY total_revenue DESC"
            message = "Here's the revenue breakdown by channel from our real data:"
        else:
            results = [{"message": "Channel or revenue data not available in dataset"}]
            sql = "SELECT 'Data not available' as status"
            message = "Required columns not found in analytics data"
            
    elif 'conversion' in question_lower:
        if 'conversions' in df.columns and 'clicks' in df.columns:
            total_clicks = df['clicks'].sum()
            total_conversions = df['conversions'].sum()
            conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            results = [{
                "total_clicks": total_clicks, 
                "total_conversions": total_conversions, 
                "conversion_rate": round(conversion_rate, 2)
            }]
            sql = "SELECT SUM(clicks) as total_clicks, SUM(conversions) as total_conversions, ROUND((SUM(conversions)::float / SUM(clicks) * 100), 2) as conversion_rate FROM analytics_data"
            message = f"Based on real data, the conversion rate is {conversion_rate:.2f}%"
        else:
            results = [{"conversion_rate": "Data not available"}]
            sql = "SELECT 'Conversion data not available' as status"
            message = "Conversion data not found in analytics dataset"
            
    elif 'roi' in question_lower:
        roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0
        results = [{
            "total_spend": total_spend, 
            "total_revenue": total_revenue, 
            "roi": round(roi, 2)
        }]
        sql = "SELECT SUM(spend) as total_spend, SUM(revenue) as total_revenue, ROUND(((SUM(revenue) - SUM(spend)) / SUM(spend) * 100), 2) as roi FROM analytics_data"
        message = f"The ROI from our real analytics data is {roi:.2f}%"
        
    elif 'channel' in question_lower and 'spend' in question_lower:
        if 'channel' in df.columns and 'spend' in df.columns:
            channel_spend = df.groupby('channel')['spend'].sum().reset_index()
            results = channel_spend.to_dict('records')
            sql = "SELECT channel, SUM(spend) as total_spend FROM analytics_data GROUP BY channel ORDER BY total_spend DESC"
            message = "Here's the spend breakdown by channel from our real data:"
        else:
            results = [{"message": "Channel or spend data not available"}]
            sql = "SELECT 'Data not available' as status"
            message = "Required columns not found"
            
    elif 'average' in question_lower and 'spend' in question_lower:
        avg_spend = df['spend'].mean() if 'spend' in df.columns else 0
        results = [{"average_spend": round(avg_spend, 2)}]
        sql = "SELECT AVG(spend) as average_spend FROM analytics_data"
        message = f"The average spend from our real data is ${avg_spend:,.2f}"
        
    elif 'top' in question_lower and ('vendor' in question_lower or 'campaign' in question_lower):
        # Try vendor first, then campaign
        if 'vendor' in df.columns and 'spend' in df.columns:
            top_items = df.groupby('vendor')['spend'].sum().nlargest(5).reset_index()
            results = top_items.to_dict('records')
            sql = "SELECT vendor, SUM(spend) as total_spend FROM analytics_data GROUP BY vendor ORDER BY total_spend DESC LIMIT 5"
            message = "Here are the top 5 vendors by spend from our real data:"
        elif 'campaign' in df.columns and 'spend' in df.columns:
            top_items = df.groupby('campaign')['spend'].sum().nlargest(5).reset_index()
            results = top_items.to_dict('records')
            sql = "SELECT campaign, SUM(spend) as total_spend FROM analytics_data GROUP BY campaign ORDER BY total_spend DESC LIMIT 5"
            message = "Here are the top 5 campaigns by spend from our real data:"
        else:
            results = [{"message": "Vendor/Campaign data not available"}]
            sql = "SELECT 'Data not available' as status"
            message = "Vendor or campaign data not found"
            
    else:
        # Default: show sample of real data
        sample_data = df.head(5).to_dict('records')
        results = sample_data
        sql = "SELECT * FROM analytics_data LIMIT 5"
        message = "Here's a sample of our real analytics data:"

    return {
        "sql": sql,
        "results": results,
        "message": message
    }

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({"error": "Question is required"}), 400

        print(f"🔍 Processing question with REAL data: {question}")
        
        if not real_analytics_data:
            return jsonify({
                "error": "No analytics data loaded", 
                "message": "Please check if Analytics_Test_Data.json exists and contains valid data"
            }), 500

        # Analyze REAL data
        response_data = analyze_real_data(question, real_analytics_data)
        
        return jsonify({
            'question': question,
            'sql': response_data['sql'],
            'results': response_data['results'],
            'message': response_data['message'],
            'session_id': 'real-data-session',
            'data_source': 'Analytics_Test_Data.json',
            'records_analyzed': len(real_analytics_data),
            'note': 'Analyzing real data from your analytics file'
        })
        
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)




