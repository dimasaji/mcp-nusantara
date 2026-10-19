from app.memory.engine import MemoryEngine


def test_chat_history_success_failure_and_context_survive_restart(tmp_path):
    session='web-11111111-1111-4111-8111-111111111111'
    memory=MemoryEngine(storage_root=tmp_path)
    memory.remember(session,'assistant','Jawaban bersumber',service_context={'service':'data pribadi'})
    memory.record_chat(session,'Syaratnya?',answer={'response':'Surat Permohonan','evidence':[{'title':'manual.pdf','chunk':'Surat Permohonan'}]})
    memory.record_chat(session,'Berapa lama?',error='HTTP_503')
    restarted=MemoryEngine(storage_root=tmp_path)
    assert restarted.service_context(session)=={'service':'data pribadi'}
    history=restarted.chat_history(session)
    assert [turn['status'] for turn in history]==['SUCCEEDED','FAILED']
    assert history[0]['answer']['evidence'][0]['title']=='manual.pdf'
    assert restarted.chat_history('web-22222222-2222-4222-8222-222222222222')==[]


def test_chat_request_idempotency_replays_completed_result_after_reopen(tmp_path):
    session = 'web-12345678-1234-1234-1234-123456789abc'
    request_id = 'a' * 32
    memory = MemoryEngine(storage_root=tmp_path)

    assert memory.begin_chat(session, request_id, 'Halo') == {'state': 'NEW'}
    assert memory.begin_chat(session, request_id, 'Halo') == {'state': 'PROCESSING'}
    answer = {'response': 'Halo kembali.'}
    memory.finish_chat(session, request_id, answer=answer)

    reopened = MemoryEngine(storage_root=tmp_path)
    replay = reopened.begin_chat(session, request_id, 'Halo')
    assert replay == {'state': 'SUCCEEDED', 'answer': answer}
    assert len(reopened.chat_history(session)) == 1


def test_chat_request_idempotency_rejects_changed_payload_and_unsafe_retry(tmp_path):
    session = 'web-12345678-1234-1234-1234-123456789abc'
    request_id = 'b' * 32
    memory = MemoryEngine(storage_root=tmp_path)

    memory.begin_chat(session, request_id, 'Pertanyaan pertama')
    assert memory.begin_chat(session, request_id, 'Pertanyaan berbeda') == {'state': 'CONFLICT'}
    assert memory.begin_chat(session, 'c' * 32, 'Pertanyaan pertama', retry_of=request_id) == {'state': 'RETRY_NOT_SAFE'}
    assert memory.finish_chat(session, request_id, error='HTTP_504_PRE_PROVIDER') is True
    assert memory.begin_chat(session, request_id, 'Pertanyaan pertama') == {
        'state': 'FAILED', 'error': 'HTTP_504_PRE_PROVIDER'}
    assert memory.begin_chat(session, 'd' * 32, 'Pertanyaan pertama', retry_of=request_id) == {'state': 'NEW'}


def test_chat_request_left_processing_by_another_instance_is_never_redispatched(tmp_path):
    session = 'web-12345678-1234-1234-1234-123456789abc'
    request_id = 'e' * 32
    original = MemoryEngine(storage_root=tmp_path)
    original.begin_chat(session, request_id, 'Permintaan yang mungkin sudah berjalan')

    restarted = MemoryEngine(storage_root=tmp_path)
    assert restarted.begin_chat(session, request_id, 'Permintaan yang mungkin sudah berjalan') == {
        'state': 'UNKNOWN', 'error': 'REQUEST_OUTCOME_UNKNOWN'}
    assert restarted.begin_chat(session, request_id, 'Permintaan yang mungkin sudah berjalan') == {
        'state': 'UNKNOWN', 'error': 'REQUEST_OUTCOME_UNKNOWN'}
