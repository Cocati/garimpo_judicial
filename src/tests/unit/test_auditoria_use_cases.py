from unittest.mock import Mock
import pytest
from src.application.use_cases import FinalizarAuditoriaUseCase
from src.domain.models import DetailedAnalysis, EvaluationStatus

def test_finalizar_auditoria_bloqueia_nulidade():
    repo = Mock()
    use_case = FinalizarAuditoriaUseCase(repo)
    analysis = DetailedAnalysis(site="x", id_leilao="1", usuario_id="u", proc_citacao=False)
    
    with pytest.raises(ValueError, match="Nulidade de Citação"):
        use_case.execute(analysis, "user123")

def test_finalizar_auditoria_status_participar_isj_alto():
    repo = Mock()
    use_case = FinalizarAuditoriaUseCase(repo)
    # Análise limpa (Score 100)
    analysis = DetailedAnalysis(site="x", id_leilao="1", usuario_id="u", proc_citacao=True, mat_prop_confere=True)
    
    status = use_case.execute(analysis, "user123")
    
    assert status == EvaluationStatus.PARTICIPAR.value
    repo.update_status.assert_called_once()