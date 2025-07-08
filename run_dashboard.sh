#!/bin/bash
# Launch the ACP Sensitivity Analysis Dashboard

echo "🚀 Starting ACP Sensitivity Analysis Dashboard..."
echo "📊 Dashboard will open in your default browser"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Install requirements if needed
pip install -r requirements.txt

# Run the Streamlit dashboard
streamlit run streamlit_dashboard.py --server.port 8501 --server.address localhost