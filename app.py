import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

# Vanna AI imports
try:
    import vanna
    from vanna.remote import VannaDefault
    VANNA_AVAILABLE = True
    print("✅ Vanna AI imported successfully")
except ImportError as e:
    VANNA_AVAILABLE = False
    print(f"❌ Vanna AI not available: {e}")

# Pandas imports
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
    print(f"✅ Pandas {pd.__version__} imported successfully")
except ImportError as e:
    PANDAS_AVAILABLE = False
    print(f"❌ Pandas not available: {e}")

app = Flask(__name__)
CORS(app)

# Initialize Vanna AI
vn = None
if VANNA_AVAILABLE:
    try:
        # For demo purposes - use default settings
        vn = VannaDefault(api_key='demo-key', model='chinook')
        print("✅ Vanna AI initialized successfully")
    except Exception as e:
        print(f"❌ Vanna AI initialization failed: {e}")
        vn = None

# Global data storage
analytics_data = []

def load_analytics_data():
    """Load and train with analytics data"""
    global analytics_data
    
    try:
        # Find the data file
        possible_paths = [
            'Analytics_Test_Data.json',
            'data/Analytics_Test_Data.json',
            '../data/Analytics_Test_Data.json',
            './data/Analytics_Test_Data.json'
        ]
        
        data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if not data_path:
            print("❌ Analytics_Test_Data.json not found")
            return False
        
        print(f"📁 Loading data from: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        analytics_data = raw_data
        print(f"✅ Loaded {len(analytics_data)} records")
        
        # Train Vanna AI with the data
        if vn is not None and PANDAS_AVAILABLE:
            train_vanna_with_data(analytics_data)
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        traceback.print_exc()
        return False

def train_vanna_with_data(data):
    """Train Vanna AI with the analytics data"""
    try:
        if not data or not PANDAS_AVAILABLE:
            return False
            
        print("🚀 Training Vanna AI with analytics data...")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        print(f"📊 DataFrame shape: {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Display sample data
        print("📄 Sample data:")
        print(df.head(3))
        
        # Train Vanna with the data
        vn.train(df=df, table_name='analytics_data')
        print("✅ Vanna trained with DataFrame")
        
        # Add documentation
        vn.train(documentation="This is marketing analytics data containing campaign performance metrics including spend, revenue, channels, and dates")
        
        # Train with specific questions
        training_questions = [
            ("What is the total marketing spend?", "SELECT SUM(spend) as total_spend FROM analytics_data"),
            ("What are the top performing campaigns by revenue?", "SELECT campaign, revenue FROM analytics_data ORDER BY revenue DESC LIMIT 5"),
            ("How much revenue did we generate?", "SELECT SUM(revenue) as total_revenue FROM analytics_data"),
            ("What is our ROI?", "SELECT (SUM(revenue) - SUM(spend)) / SUM(spend) * 100 as roi FROM analytics_data"),
            ("Which marketing channels are most effective?", "SELECT channel, SUM(spend) as total_spend, SUM(revenue) as total_revenue FROM analytics_data GROUP BY channel ORDER BY total_revenue DESC"),
            ("Show me recent campaign performance", "SELECT campaign, channel, spend, revenue, date FROM analytics_data ORDER BY date DESC LIMIT 10"),
            ("What are the monthly trends?", "SELECT strftime('%Y-%m', date) as month, SUM(spend) as monthly_spend, SUM(revenue) as monthly_revenue FROM analytics_data GROUP BY month ORDER BY month DESC"),
            ("Which campaigns have the highest ROI?", "SELECT campaign, spend, revenue, (revenue - spend) / spend * 100 as roi FROM analytics_data WHERE spend > 0 ORDER BY roi DESC LIMIT 10")
        ]
        
        for question, sql in training_questions:
            vn.train(question=question, sql=sql)
            print(f"✅ Trained: {question}")
        
        print("🎉 Vanna AI training completed!")
        return True
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        traceback.print_exc()
        return False

# Load data on startup
load_analytics_data()

@app.route('/')
def home():
    return jsonify({
        "message": "Vanna AI Analytics API - Production Ready",
        "status": "healthy",
        "python_version": sys.version.split()[0],
        "data_source": "Analytics_Test_Data.json",
        "records_loaded": len(analytics_data),
        "vanna_ai": VANNA_AVAILABLE and vn is not None,
        "pandas": PANDAS_AVAILABLE,
        "endpoints": {
            "health": "/health (GET)",
            "ask": "/ask (POST)",
            "data_stats": "/data/stats (GET)"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "vanna-ai-analytics",
        "records_loaded": len(analytics_data),
        "vanna_ai_ready": VANNA_AVAILABLE and vn is not None,
        "data_available": len(analytics_data) > 0
    })

@app.route('/data/stats', methods=['GET'])
def data_stats():
    """Get data statistics"""
    if not analytics_data:
        return jsonify({"error": "No data loaded", "records": 0})
    
    try:
        sample = analytics_data[0] if analytics_data else {}
        return jsonify({
            "total_records": len(analytics_data),
            "columns": list(sample.keys()) if isinstance(sample, dict) else [],
            "data_preview": analytics_data[:2]
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/ask', methods=['POST'])
def ask_question():
    """Main endpoint - uses Vanna AI for SQL generation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "Question is required"}), 400

        print(f"🤖 Processing: '{question}'")
        print(f"📊 Data records: {len(analytics_data)}")
        
        # Try Vanna AI first
        if vn is not None and PANDAS_AVAILABLE:
            try:
                print("🔍 Using Vanna AI to generate SQL...")
                
                # Generate SQL using Vanna
                sql = vn.generate_sql(question=question)
                print(f"📝 Generated SQL: {sql}")
                
                # Run the SQL on our data
                df = pd.DataFrame(analytics_data)
                results = vn.run_sql(sql=sql, df=df)
                
                # Convert results to JSON-serializable format
                if hasattr(results, 'to_dict'):
                    results_dict = results.to_dict('records')
                else:
                    results_dict = results
                
                print(f"✅ Found {len(results_dict)} results")
                
                return jsonify({
                    'question': question,
                    'sql': sql,
                    'results': results_dict,
                    'message': f"Analysis complete: {len(results_dict)} results found",
                    'source': 'vanna-ai',
                    'success': True,
                    'records_analyzed': len(analytics_data)
                })
                
            except Exception as e:
                print(f"❌ Vanna AI failed: {e}")
                # Fall through to basic processing
        
        # Fallback: Basic processing without Vanna
        print("🔄 Using fallback processing...")
        response = process_with_basic_analytics(question)
        
        return jsonify({
            'question': question,
            'sql': response.get('sql', 'SELECT * FROM analytics_data'),
            'results': response.get('results', []),
            'message': response.get('message', 'Basic analysis complete'),
            'source': 'fallback',
            'success': response.get('success', False),
            'records_analyzed': len(analytics_data)
        })
        
    except Exception as e:
        print(f"💥 Error in /ask: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'question': question,
            'success': False
        }), 500

def process_with_basic_analytics(question):
    """Basic analytics without Vanna AI"""
    question_lower = question.lower()
    
    if not analytics_data or not PANDAS_AVAILABLE:
        return {
            'sql': "SELECT 'No data available' as status",
            'results': [{'status': 'No analytics data loaded'}],
            'message': 'No data available for analysis',
            'success': False
        }
    
    try:
        df = pd.DataFrame(analytics_data)
        
        # Basic question routing
        if 'total' in question_lower and 'spend' in question_lower:
            total_spend = df['spend'].sum() if 'spend' in df.columns else 0
            return {
                'sql': "SELECT SUM(spend) as total_spend FROM analytics_data",
                'results': [{'total_spend': total_spend, 'currency': 'USD'}],
                'message': f'Total Marketing Spend: ${total_spend:,.2f}',
                'success': True
            }
            
        elif 'total' in question_lower and 'revenue' in question_lower:
            total_revenue = df['revenue'].sum() if 'revenue' in df.columns else 0
            return {
                'sql': "SELECT SUM(revenue) as total_revenue FROM analytics_data",
                'results': [{'total_revenue': total_revenue, 'currency': 'USD'}],
                'message': f'Total Revenue: ${total_revenue:,.2f}',
                'success': True
            }
            
        elif 'recent' in question_lower or 'latest' in question_lower:
            # Get recent records
            if 'date' in df.columns:
                recent_data = df.sort_values('date', ascending=False).head(10)
            else:
                recent_data = df.head(10)
            
            results = recent_data.replace({pd.NaT: None, pd.NA: None}).to_dict('records')
            return {
                'sql': "SELECT * FROM analytics_data ORDER BY date DESC LIMIT 10",
                'results': results,
                'message': f'Showing {len(results)} most recent records',
                'success': True
            }
            
        elif 'channel' in question_lower:
            # Group by channel
            if 'channel' in df.columns:
                channel_stats = df.groupby('channel').agg({
                    'spend': 'sum',
                    'revenue': 'sum'
                }).reset_index()
                channel_stats['roi'] = ((channel_stats['revenue'] - channel_stats['spend']) / channel_stats['spend'] * 100).round(2)
                results = channel_stats.replace({pd.NA: None}).to_dict('records')
                
                return {
                    'sql': "SELECT channel, SUM(spend) as spend, SUM(revenue) as revenue FROM analytics_data GROUP BY channel",
                    'results': results,
                    'message': f'Channel performance analysis ({len(results)} channels)',
                    'success': True
                }
        
        # Default: return sample data
        sample_data = df.head(5).replace({pd.NA: None, pd.NaT: None}).to_dict('records')
        return {
            'sql': "SELECT * FROM analytics_data LIMIT 5",
            'results': sample_data,
            'message': f'Sample data from {len(analytics_data)} total records',
            'success': True
        }
        
    except Exception as e:
        print(f"❌ Basic analytics error: {e}")
        return {
            'sql': "SELECT 'Error in analysis' as status",
            'results': [{'error': str(e)}],
            'message': 'Error processing your question',
            'success': False
        }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Vanna AI Analytics API on port {port}")
    print(f"🐍 Python: {sys.version}")
    print(f"📊 Records loaded: {len(analytics_data)}")
    print(f"🤖 Vanna AI: {'✅ Ready' if (VANNA_AVAILABLE and vn is not None) else '❌ Unavailable'}")
    print(f"📈 Pandas: {'✅ Available' if PANDAS_AVAILABLE else '❌ Unavailable'}")
    app.run(host='0.0.0.0', port=port, debug=False)






