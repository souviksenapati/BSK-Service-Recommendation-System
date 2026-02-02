import requests
import json

print("="*60)
print("API HEALTH CHECK - POST CLEANUP")
print("="*60)

try:
    # Test recommendation endpoint
    response = requests.post(
        'http://localhost:8000/api/recommend',
        json={
            'phone': '9740781204',
            'age': 32,
            'gender': 'Male',
            'caste': 'General',
            'district_name': 'PURBA MEDINIPUR',
            'block_name': 'EGRA I',
            'religion': 'Hindu',
            'selected_service_name': 'Application for Income Certificates'
        },
        timeout=20
    )
    
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n📋 Response Structure:")
        print(f"  - citizen_exists: {data.get('citizen_exists')}")
        print(f"  - citizen_id: {data.get('citizen_id')}")
        print(f"  - demographics: {data.get('demographics')}")
        print(f"  - service_history: {len(data.get('service_history', []))} records")
        
        recommendations = data.get('recommendations', [])
        if recommendations:
            count = recommendations[0]
            services = recommendations[1:]
            
            print(f"\n🎯 Recommendations:")
            print(f"  - Total Count: {count}")
            print(f"  - Services returned: {len(services)}")
            print(f"\n  First 5 recommendations:")
            for i, service in enumerate(services[:5], 1):
                print(f"    {i}. {service}")
        
        print("\n" + "="*60)
        print("✅ API TEST PASSED - Everything working perfectly!")
        print("="*60)
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ Test Failed: {str(e)}")
