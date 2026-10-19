from django.http import HttpResponse, JsonResponse


OPENAPI = {
    "openapi": "3.0.3",
    "info": {"title": "Student Record System API", "version": "1.0.0"},
    "servers": [{"url": "/api"}],
    "components": {
        "securitySchemes": {"jwtCookie": {"type": "apiKey", "in": "cookie", "name": "srs_access"}},
        "schemas": {
            "Error": {"type": "object", "required": ["code", "message", "correlationId", "fieldErrors"], "properties": {"code": {"type": "string"}, "message": {"type": "string"}, "correlationId": {"type": "string"}, "fieldErrors": {"type": "object"}}},
            "Page": {"type": "object", "properties": {"items": {"type": "array"}, "page": {"type": "integer"}, "pageSize": {"type": "integer"}, "total": {"type": "integer"}}},
        },
    },
    "paths": {
        "/auth/login": {"post": {"summary": "Authenticate with login ID and password"}},
        "/auth/logout": {"post": {"summary": "Revoke the current JWT cookie", "security": [{"jwtCookie": []}]}},
        "/auth/me": {"get": {"summary": "Current authenticated user"}},
        "/auth/forgot-password": {"post": {"summary": "Issue a registered-email OTP"}},
        "/auth/reset-password": {"post": {"summary": "Consume an OTP and replace the password"}},
        "/students/me": {"get": {"summary": "Current student profile"}},
        "/students/me/documents": {"get": {"summary": "List owned documents"}, "post": {"summary": "Upload and scan a PDF/JPEG"}},
        "/catalog/programs": {"get": {"summary": "List programs"}, "post": {"summary": "Create a program (admin)"}},
        "/catalog/courses": {"get": {"summary": "List courses"}, "post": {"summary": "Create a course (admin)"}},
        "/catalog/semesters": {"get": {"summary": "List semesters"}, "post": {"summary": "Create a semester (admin)"}},
        "/catalog/offerings": {"get": {"summary": "List course offerings"}, "post": {"summary": "Create an offering (admin)"}},
        "/enrollments/eligible": {"get": {"summary": "Eligible current-semester offerings"}},
        "/enrollments": {"get": {"summary": "Current user's enrollments"}, "post": {"summary": "Atomically enroll in an offering"}},
        "/attendance/student-summary": {"get": {"summary": "Own attendance percentages"}},
        "/attendance/sessions/{sessionId}/records": {"post": {"summary": "Bulk save assigned attendance"}},
        "/grades/components/{componentId}/marks": {"post": {"summary": "Bulk save marks before lock"}},
        "/grades/offerings/{offeringId}/finalize": {"post": {"summary": "Finalize and lock offering grades"}},
        "/grades/gpa": {"get": {"summary": "Own semester GPA and CGPA"}},
        "/grades/transcript": {"get": {"summary": "Official transcript PDF"}},
        "/grades/transcript/verify/{code}": {"get": {"summary": "Verify a transcript code"}},
        "/fees/invoices": {"get": {"summary": "List invoices"}},
        "/fees/payments/initiate": {"post": {"summary": "Create a mock payment order"}},
        "/fees/payments/callback": {"post": {"summary": "Signed idempotent payment callback"}},
        "/health/live": {"get": {"summary": "Process liveness"}},
        "/health/ready": {"get": {"summary": "Database readiness"}},
        "/reports/{kind}": {"get": {"summary": "Authorized paginated report/export"}},
    },
}


def openapi_json(request):
    return JsonResponse(OPENAPI)


def api_docs(request):
    html = """<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Student Record API</title><style>body{font:16px system-ui;max-width:900px;margin:3rem auto;padding:0 1rem}pre{background:#f2f5f7;padding:1rem;overflow:auto}a{color:#075985}</style></head><body><h1>Student Record System API</h1><p>Machine-readable contract: <a href='/api/openapi.json'>/api/openapi.json</a></p><pre>All JSON errors use {code, message, correlationId, fieldErrors}. Authentication uses the HttpOnly srs_access cookie and X-CSRFToken for unsafe browser requests.</pre></body></html>"""
    return HttpResponse(html)
