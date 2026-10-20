from app.core.config import Settings
from app.core.runtime_identity import capture_model_identity


def test_status_needs_matching_inference_and_expires_on_new_selection(tmp_path):
    owner=Settings(_env_file=None)
    config=owner.compose_configuration(project_root=tmp_path,environment={},dotenv_environment={},
        overrides={'llm':{'provider':'ollama','model':'fixture-a'}})
    assert owner.model_control_status()['status']=='NOT_VERIFIED'
    owner.record_v1_execution(revision=0,model='fixture-a',provider_status='ollama',grounded=False,stages=())
    assert owner.model_control_status()['status']=='NOT_VERIFIED'
    identity=capture_model_identity(provider_id='ollama',selected_model='fixture-a',configuration=config)
    receipt=identity.with_response('fixture-a',completed=True).safe_dump()
    owner.record_v1_execution(revision=0,model='fixture-a',provider_status='ollama',grounded=False,
        stages=(),execution_identity=receipt)
    assert owner.model_control_status()['status']=='INFERENCE_VERIFIED'
    assert owner.model_control_status()['verified_at']
    config,_=owner.select_operator_model('fixture-b',expected_revision=0,validated_configuration=config)
    assert owner.model_control_status()['status']=='NOT_VERIFIED'
    owner.record_v1_execution(revision=0,model='fixture-a',provider_status='ollama',grounded=False,
        stages=(),execution_identity=receipt)
    assert owner.model_control_status()['status']=='NOT_VERIFIED'


def test_old_receipt_does_not_claim_current_verification(tmp_path):
    owner=Settings(_env_file=None)
    owner.compose_configuration(project_root=tmp_path,environment={},dotenv_environment={})
    owner._last_verified_execution={'model':owner.llm_model,'provider':owner.llm_provider,'revision':0,
        'timestamp':'2000-01-01T00:00:00+00:00'}
    assert owner.model_control_status()['status']=='NOT_VERIFIED'
