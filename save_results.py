#!/usr/bin/env python3

import json
import datetime
from src.alert_analyzer import AlertAnalyzer

# Create analyzer
analyzer = AlertAnalyzer()

# Analyze file
results = analyzer.analyze_file('data/Alert_Event_Data.gz', dimension_name='host', k=5)

# Generate timestamp
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# Save results to file
filename = f'results/top_hosts_{timestamp}.json'
with open(filename, 'w') as f:
    json.dump(results, f, indent=2)

print(f'Results saved to {filename}')
