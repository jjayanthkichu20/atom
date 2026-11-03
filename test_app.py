import json
import sys

# Ensure UTF-8 output if possible
if sys.stdout.encoding and 'cp' in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import app, DEFAULT_SESSION_ID

def test_routes():
    client = app.test_client()

    # 1. Test Home Route
    res = client.get('/')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Atom by JobAlchemy" in res.data
    print("[PASS] Route '/' passed")

    # 2. Test Specific Session Route
    res = client.get(f'/chat/{DEFAULT_SESSION_ID}')
    assert res.status_code == 200
    assert b"Atom by JobAlchemy" in res.data
    print(f"[PASS] Route '/chat/{DEFAULT_SESSION_ID}' passed")

    # 3. Test Session API
    res = client.get(f'/api/session/{DEFAULT_SESSION_ID}')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] is True
    assert len(data['jobs']) >= 4
    assert data['profile']['name'] == "Alex Morgan"
    print(f"[PASS] Route '/api/session/<id>' passed with {len(data['jobs'])} jobs")

    # 4. Test Chat Agent Fallback
    res = client.post('/api/chat', json={
        "sessionId": DEFAULT_SESSION_ID,
        "message": "Please tailor my CV for Stripe",
        "provider": "gemini"
    })
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] is True
    assert "Tailoring Your CV" in data['message']['content'] or "Stripe" in data['message']['content']
    print("[PASS] Route '/api/chat' passed")

    # 5. Test Apply Endpoint (Human-in-the-loop submission)
    res = client.post('/api/apply', json={
        "jobId": "job-stripe-01",
        "sessionId": DEFAULT_SESSION_ID,
        "candidate": {"name": "Alex Morgan", "email": "alex@test.com"},
        "answers": {"question_0": "Test answer"}
    })
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] is True
    assert data['application']['company'] == "Stripe"
    print("[PASS] Route '/api/apply' passed")

    # 6. Test Applications List
    res = client.get('/api/applications')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data['applications']) >= 2
    print(f"[PASS] Route '/api/applications' passed with {len(data['applications'])} applications")

    # 7. Test PDF Resume Generation
    res = client.get('/api/download-cv/job-stripe-01')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert len(res.data) > 1000
    print(f"[PASS] Route '/api/download-cv' passed (Generated PDF size: {len(res.data)} bytes)")

    # 8. Test Real CV Document Upload & Job Matching
    import io
    sample_cv = """John Doe
john.doe.engineer@example.com
+1 (555) 789-1234
Senior Backend Distributed Systems Engineer

Professional Summary:
Senior Backend Engineer with 7 years of experience architecting distributed microservices using Python, Go, Docker, Kubernetes, and PostgreSQL on AWS.

Technical Skills:
Python, Go, PostgreSQL, Docker, Kubernetes, AWS, Redis, GraphQL, System Design, CI/CD

Work Experience:
Lead Systems Engineer at TechCorp (2021-Present)
- Scaled high-throughput message bus handling 250k events/sec with 99.99% availability.
- Cut database query latency by 45% using Postgres indexing and Redis caching.
"""
    data = {
        'cv_file': (io.BytesIO(sample_cv.encode('utf-8')), 'John_Doe_CV.txt'),
        'sessionId': DEFAULT_SESSION_ID
    }
    res = client.post('/api/upload-cv', data=data, content_type='multipart/form-data')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.data}"
    upload_res = json.loads(res.data)
    assert upload_res['success'] is True
    assert upload_res['profile']['name'] == "John Doe"
    assert "Python" in upload_res['profile']['skills']
    assert len(upload_res['jobs']) >= 3
    print(f"[PASS] Route '/api/upload-cv' passed (Parsed: {upload_res['profile']['name']}, Matched: {len(upload_res['jobs'])} jobs)")

    print("\nALL 8 TESTS PASSED SUCCESSFULLY! 🚀")

if __name__ == '__main__':
    test_routes()
