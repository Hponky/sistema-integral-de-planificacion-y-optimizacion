
import sys
import json
import traceback
from datetime import datetime
# Ensure we can import sipo modules if needed, or local
# Since this is run as -m services.scheduler_isolate, imports should work

# Optimized scheduler is now the default in services.scheduler
from services.scheduler import SchedulerService

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m services.scheduler.isolate_service <input_json> <output_json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        agents = data.get('agents', [])
        start_date_str = data.get('start_date')
        days_count = data.get('days_count', 30)
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        rules_config = data.get('rules_config', {})
        requirements = data.get('requirements', {})
        calls = data.get('calls', {})
        
        # Instantiate and run
        scheduler = SchedulerService()
        result = scheduler.generate_schedule(
            agents, 
            start_date, 
            days_count, 
            rules_config=rules_config,
            requirements=requirements,
            calls_forecast=calls
        )
        
        # Helper for datetime serialization
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError (f"Type {type(obj)} not serializable")
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, default=json_serial)
            
        # print("SUCCESS")
        

    except Exception as e:
        print(f"ERROR in scheduler_isolate: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)

if __name__ == "__main__":
    main()
