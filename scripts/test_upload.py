import json
import httpx

url = "http://127.0.0.1:8000/rag/materials/upload-markdown"
payload = {
    "title": "02 مذكرة حل المعادلات التربيعية",
    "content_markdown": "حل المعادلات\n\nفي هذا الدرس ...",
    "topic": "حل المعادلات التربيعية",
    "subject": "الرياضيات",
    "grade": "12",
    "difficulty_level": "intermediate",
    "material_id": "string"
}

try:
    r = httpx.post(url, json=payload, timeout=15)
    print('Status:', r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(r.text)
except Exception as e:
    print('Request failed:', e)
