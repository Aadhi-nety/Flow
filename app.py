import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

# Initialize analytics data
real_analytics_data = []

def safe_import_pandas():
    """Safely import pandas with compatibility handling"""
    try:
        # Force numpy compatibility first
        import numpy as np
        print(f"numpy version: {np.__version__}")
        
        import pandas as pd
        print(f"pandas version: {pd.__version__}")
        return pd, np
    except Exception as e:
        print(f"Error importing pandas: {e}")
        print(f"Python path: {sys.path}")
        return None, None

def load_real_analytics_data():
    """Load real analytics data with robust error handling"""
    global real_analytics_data
    try:
        # Try multiple possible paths for the data file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'Analytics_Test_Data.json'),
            os.path.join(os.path.dirname(__file__), 'data', 'Analytics_Test_Data.json'),
            os.path.join(os.getcwd(), 'data', 'Analytics_Test_Data.json'),
            'Analytics_Test_Data.json'
        ]
        
        data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_path = path
                break
                
        if not data_path:
            print("Could not find Analytics_Test_Data.json in any expected location")
            real_analytics_data = []
            return
            
        print(f"Loading data from: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        print(f"Successfully loaded {len(data)} records from real analytics data")
        real_analytics_data = data
        
        # Print sample of data structure
        if data:
            print(f"Data columns sample: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not dict'}")
            
    except Exception as e:
        print(f"Error loading real analytics data: {e}")
        print(traceback.format_exc())
        real_analytics_data = []

# Load data on startup
load_real_analytics_data()

@app.route('/')
def home():
    return jsonify({
        "message": "Vanna AI Analytics API - Full Production Version", 
        "status": "healthy",
        "python_version": sys.version.split()[0],
        "data_source": "Analytics_Test_Data.json",
        "records_loaded": len(real_analytics_data),
        "endpoints": {
            "health": "/health",
            "ask_question": "/ask (POST)",
            "get_data_stats": "/data/stats"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    pd, np = safe_import_pandas()
    lib_status = "available" if pd else "unavailable"
    
    return jsonify({
        "status": "healthy", 
        "service": "vanna-ai-analytics", 
        "python_version": sys.version.split()[0],
        "data_source": "real_analytics_data",
        "records_loaded": len(real_analytics_data),
        "pandas_status": lib_status,
        "endpoints_working": True
    })

@app.route('/data/stats', methods=['GET'])
def get_data_stats():
    """Endpoint to check data statistics"""
    if not real_analytics_data:
        return jsonify({"error": "No data loaded", "records": 0})
    
    try:
        sample_record = real_analytics_data[0] if real_analytics_data else {}
        return jsonify({
            "total_records": len(real_analytics_data),
            "sample_columns": list(sample_record.keys()) if isinstance(sample_record, dict) else [],
            "data_preview": real_analytics_data[:3] if len(real_analytics_data) > 3 else real_analytics_data
        })
    except Exception as e:
        return jsonify({"error": str(e), "records": len(real_analytics_data)})

def analyze_real_data(question, data):
    """Enhanced analytics with real data processing"""
    question_lower = question.lower()
    
    if not data:
        return {
            "sql": "SELECT 'No data available' as status",
            "results": [{"status": "No analytics data loaded", "records": 0}],
            "message": "No analytics data available. Please check data file.",
            "data_available": False
        }
    
    try:
        pd, np = safe_import_pandas()
        if pd is None:
            # Fallback to basic JSON processing without pandas
            return process_without_pandas(question_lower, data)
        
        # Convert to DataFrame for advanced analysis
        df = pd.DataFrame(data)
        print(f"DataFrame shape: {df.shape}, Columns: {list(df.columns)}")
        
        # Enhanced analytics based on common questions
        if any(term in question_lower for term in ['total spend', 'total spend', 'sum spend']):
            total_spend = calculate_total_spend(df)
            return {
                "sql": "SELECT SUM(spend) as total_spend FROM analytics_data",
                "results": [{"total_spend": total_spend, "currency": "USD"}],
                "message": f"Total Marketing Spend: ${total_spend:,.2f}",
                "data_available": True,
                "analysis_type": "spend_analysis"
            }
            
        elif any(term in question_lower for term in ['revenue', 'income', 'sales']):
            total_revenue = calculate_total_revenue(df)
            return {
                "sql": "SELECT SUM(revenue) as total_revenue FROM analytics_data",
                "results": [{"total_revenue": total_revenue, "currency": "USD"}],
                "message": f"Total Revenue Generated: ${total_revenue:,.2f}",
                "data_available": True,
                "analysis_type": "revenue_analysis"
            }
            
        elif any(term in question_lower for term in ['roi', 'return on investment', 'return']):
            total_spend = calculate_total_spend(df)
            total_revenue = calculate_total_revenue(df)
            roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0
            profit = total_revenue - total_spend
            
            return {
                "sql": "SELECT ((SUM(revenue)-SUM(spend))/SUM(spend)*100) as roi, SUM(revenue)-SUM(spend) as profit FROM analytics_data",
                "results": [
                    {
                        "roi_percentage": round(roi, 2),
                        "profit": profit,
                        "total_spend": total_spend,
                        "total_revenue": total_revenue,
                        "currency": "USD"
                    }
                ],
                "message": f"ROI Analysis:\n• Return on Investment: {roi:.2f}%\n• Net Profit: ${profit:,.2f}\n• Total Spend: ${total_spend:,.2f}\n• Total Revenue: ${total_revenue:,.2f}",
                "data_available": True,
                "analysis_type": "roi_analysis"
            }
            
        elif any(term in question_lower for term in ['channel', 'source', 'medium']):
            # Analyze by marketing channel
            channel_analysis = analyze_by_channel(df)
            return {
                "sql": "SELECT channel, SUM(spend) as spend, SUM(revenue) as revenue FROM analytics_data GROUP BY channel",
                "results": channel_analysis,
                "message": f"Marketing Channel Performance Analysis ({len(channel_analysis)} channels)",
                "data_available": True,
                "analysis_type": "channel_analysis"
            }
            
        elif any(term in question_lower for term in ['top', 'best', 'worst', 'performance']):
            # Top performing campaigns
            top_performers = analyze_top_performers(df)
            return {
                "sql": "SELECT campaign, spend, revenue, (revenue-spend) as profit FROM analytics_data ORDER BY profit DESC LIMIT 5",
                "results": top_performers,
                "message": f"Top {len(top_performers)} Performing Campaigns by Profit",
                "data_available": True,
                "analysis_type": "performance_analysis"
            }
            
        else:
            # General data overview
            stats = get_data_statistics(df)
            sample_data = df.head(5).replace({pd.NA: None, pd.NaT: None}).to_dict('records')
            
            return {
                "sql": "SELECT * FROM analytics_data LIMIT 5",
                "results": sample_data,
                "message": f"Data Overview: {stats}",
                "data_available": True,
                "analysis_type": "general_overview",
                "statistics": stats
            }
            
    except Exception as e:
        print(f"Error in analyze_real_data: {e}")
        print(traceback.format_exc())
        # Fallback to non-pandas processing
        return process_without_pandas(question_lower, data)

def calculate_total_spend(df):
    """Calculate total spend from dataframe"""
    spend_columns = [col for col in df.columns if 'spend' in col.lower()]
    if spend_columns:
        return float(df[spend_columns[0]].sum())
    return 0.0

def calculate_total_revenue(df):
    """Calculate total revenue from dataframe"""
    revenue_columns = [col for col in df.columns if 'revenue' in col.lower()]
    if revenue_columns:
        return float(df[revenue_columns[0]].sum())
    return 0.0

def analyze_by_channel(df):
    """Analyze performance by marketing channel"""
    try:
        channel_cols = [col for col in df.columns if any(term in col.lower() for term in ['channel', 'source', 'medium'])]
        if channel_cols:
            channel_col = channel_cols[0]
            spend_col = [col for col in df.columns if 'spend' in col.lower()][0]
            revenue_col = [col for col in df.columns if 'revenue' in col.lower()][0]
            
            grouped = df.groupby(channel_col).agg({
                spend_col: 'sum',
                revenue_col: 'sum'
            }).reset_index()
            
            result = []
            for _, row in grouped.iterrows():
                result.append({
                    'channel': row[channel_col],
                    'spend': float(row[spend_col]),
                    'revenue': float(row[revenue_col]),
                    'profit': float(row[revenue_col] - row[spend_col]),
                    'roi': float(((row[revenue_col] - row[spend_col]) / row[spend_col] * 100) if row[spend_col] > 0 else 0)
                })
            return result
    except Exception as e:
        print(f"Error in channel analysis: {e}")
    
    return [{"error": "Could not analyze by channel"}]

def analyze_top_performers(df):
    """Analyze top performing campaigns"""
    try:
        campaign_cols = [col for col in df.columns if 'campaign' in col.lower()]
        spend_col = [col for col in df.columns if 'spend' in col.lower()][0]
        revenue_col = [col for col in df.columns if 'revenue' in col.lower()][0]
        
        if campaign_cols:
            campaign_col = campaign_cols[0]
            df['profit'] = df[revenue_col] - df[spend_col]
            top_campaigns = df.nlargest(5, 'profit')
            
            result = []
            for _, row in top_campaigns.iterrows():
                result.append({
                    'campaign': row[campaign_col],
                    'spend': float(row[spend_col]),
                    'revenue': float(row[revenue_col]),
                    'profit': float(row['profit']),
                    'roi': float(((row[revenue_col] - row[spend_col]) / row[spend_col] * 100) if row[spend_col] > 0 else 0)
                })
            return result
    except Exception as e:
        print(f"Error in top performers analysis: {e}")
    
    return [{"error": "Could not analyze top performers"}]

def get_data_statistics(df):
    """Get basic data statistics"""
    try:
        spend_col = [col for col in df.columns if 'spend' in col.lower()][0]
        revenue_col = [col for col in df.columns if 'revenue' in col.lower()][0]
        
        return {
            "total_campaigns": len(df),
            "date_range": f"{df['date'].min()} to {df['date'].max()}" if 'date' in df.columns else "Not available",
            "columns_available": list(df.columns),
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        }
    except Exception as e:
        return {"error": str(e)}

def process_without_pandas(question_lower, data):
    """Fallback processing without pandas"""
    print("Using fallback processing without pandas")
    
    if not data or not isinstance(data, list) or not data:
        return {
            "sql": "SELECT 'No valid data' as status",
            "results": [{"status": "Data processing error"}],
            "message": "Cannot process data without pandas",
            "data_available": False
        }
    
    # Basic analysis without pandas
    try:
        total_spend = 0
        total_revenue = 0
        
        for record in data:
            if isinstance(record, dict):
                # Sum spend and revenue from all records
                for key, value in record.items():
                    if 'spend' in key.lower() and isinstance(value, (int, float)):
                        total_spend += value
                    elif 'revenue' in key.lower() and isinstance(value, (int, float)):
                        total_revenue += value
        
        if 'spend' in question_lower:
            return {
                "sql": "SELECT SUM(spend) as total_spend FROM analytics_data",
                "results": [{"total_spend": total_spend}],
                "message": f"Total Spend (basic calculation): ${total_spend:,.2f}",
                "data_available": True
            }
        elif 'revenue' in question_lower:
            return {
                "sql": "SELECT SUM(revenue) as total_revenue FROM analytics_data",
                "results": [{"total_revenue": total_revenue}],
                "message": f"Total Revenue (basic calculation): ${total_revenue:,.2f}",
                "data_available": True
            }
        else:
            return {
                "sql": "SELECT * FROM analytics_data LIMIT 3",
                "results": data[:3],
                "message": f"Sample data ({len(data)} total records). Basic mode active.",
                "data_available": True
            }
            
    except Exception as e:
        return {
            "sql": "SELECT 'Error in basic processing' as status",
            "results": [{"error": str(e)}],
            "message": "Error in basic data processing",
            "data_available": False
        }

@app.route('/ask', methods=['POST'])
def ask_question():
    """Main endpoint for analytics questions"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "Question is required"}), 400

        print(f"Processing question: {question}")
        print(f"Data records available: {len(real_analytics_data)}")
        
        # Analyze the question with real data
        response_data = analyze_real_data(question, real_analytics_data)
        
        return jsonify({
            'question': question,
            'sql': response_data.get('sql', ''),
            'results': response_data.get('results', []),
            'message': response_data.get('message', ''),
            'session_id': 'real-analytics-session',
            'data_source': 'Analytics_Test_Data.json',
            'records_analyzed': len(real_analytics_data),
            'analysis_type': response_data.get('analysis_type', 'general'),
            'data_available': response_data.get('data_available', False),
            'statistics': response_data.get('statistics', {})
        })
        
    except Exception as e:
        print(f"Error in ask_question endpoint: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'question': data.get('question', '') if 'data' in locals() else '',
            'records_available': len(real_analytics_data)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "available_endpoints": ["/", "/health", "/ask", "/data/stats"]}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "records_loaded": len(real_analytics_data)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Vanna AI Analytics API on port {port}")
    print(f"Python version: {sys.version}")
    print(f"Data records loaded: {len(real_analytics_data)}")
    app.run(host='0.0.0.0', port=port, debug=False)





