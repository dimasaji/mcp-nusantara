from pathlib import Path

p = Path("app/api/routes.py")
s = p.read_text(encoding="utf-8")

bad = '''        return {
            "session_id": request.session_id,
        # Gate 10 Memory â€” store final assistant response.
        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )

            "response": response_text,
            "gate_pipeline": gate_context,
'''

good = '''        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )

        return {
            "session_id": request.session_id,
            "response": response_text,
            "gate_pipeline": gate_context,
'''

if bad not in s:
    # Fallback: remove the misplaced block and insert it immediately
    # before the final response dictionary.
    memory_block = '''        # Gate 10 Memory â€” store final assistant response.
        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )

'''
    if memory_block in s:
        s = s.replace(memory_block, "", 1)

    marker = '''        return {
            "session_id": request.session_id,
'''
    if marker not in s:
        print("PATCH GAGAL: marker FINAL RESPONSE tidak ditemukan")
        raise SystemExit(1)

    s = s.replace(
        marker,
        '''        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )

        return {
            "session_id": request.session_id,
''',
        1,
    )
else:
    s = s.replace(bad, good, 1)

p.write_text(s, encoding="utf-8")

# Syntax validation
compile(s, str(p), "exec")

print("==============================================")
print("ROUTES GATE 10 MEMORY PATCH : PASS")
print("SYNTAX : OK")
print("==============================================")
