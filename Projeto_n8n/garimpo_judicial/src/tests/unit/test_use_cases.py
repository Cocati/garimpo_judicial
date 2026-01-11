import pytest
from unittest.mock import Mock
from datetime import datetime

# IMPORTANTE: Estas são as classes que estavam faltando (causando o NameError)
from src.domain.models import Auction, Evaluation, EvaluationStatus, AuctionFilter
# Importação dos Casos de Uso
from src.application.use_cases import (
    GetPendingAuctionsUseCase, 
    SubmitBatchEvaluationUseCase, 
    GetPortfolioUseCase
)

class TestAuctionsUseCases:
    
    def setup_method(self):
        # Mock do repositório para isolar a lógica de negócio do Banco de Dados
        self.mock_repo = Mock()
        
    def test_get_pending_auctions_should_call_repository_with_correct_filters(self):
        """
        Garante que o Use Case repassa os filtros corretamente para o Repositório.
        """
        use_case = GetPendingAuctionsUseCase(self.mock_repo)
        user_id = "user_123"
        uf_filter = ["SP"]
        
        # Act
        use_case.execute(user_id=user_id, uf=uf_filter)
        
        # Assert
        args, _ = self.mock_repo.get_pending_auctions.call_args
        called_user_id, called_filter = args
        
        assert called_user_id == user_id
        assert called_filter.uf == uf_filter
        # Aqui não dará mais NameError, pois AuctionFilter foi importado no topo
        assert isinstance(called_filter, AuctionFilter)

    def test_submit_batch_evaluation_should_create_evaluations_correctly(self):
        """
        Verifica se o processamento de lote converte dicts em entidades de Evaluation.
        """
        use_case = SubmitBatchEvaluationUseCase(self.mock_repo)
        user_id = "user_test"
        items = [
            {'site': 'leiloeiro_a', 'id_leilao': '101'},
            {'site': 'leiloeiro_b', 'id_leilao': '102'}
        ]
        decision = EvaluationStatus.ANALISAR # Agora reconhecido via import
        
        # Act
        use_case.execute(user_id, items, decision)
        
        # Assert
        called_evaluations = self.mock_repo.save_evaluations.call_args[0][0]
        
        assert len(called_evaluations) == 2
        assert isinstance(called_evaluations[0], Evaluation)
        assert called_evaluations[0].avaliacao == EvaluationStatus.ANALISAR

    def test_get_portfolio_should_isolate_domain_from_infrastructure(self):
        """
        Verifica se o Use Case retorna os dados do domínio corretamente.
        """
        use_case = GetPortfolioUseCase(self.mock_repo)
        
        # Criamos uma instância real da entidade Auction para o mock retornar
        mock_auction = Auction(
            site="site1", id_leilao="1", titulo="Casa", uf="RJ", cidade="Rio",
            tipo_leilao="Judicial", tipo_bem="Imóvel", valor_1_praca=100.0,
            valor_2_praca=50.0, link_detalhe="...", imagem_capa="..."
        )
        self.mock_repo.get_portfolio_auctions.return_value = [mock_auction]
        
        # Act
        result = use_case.execute("user_1")
        
        # Assert
        assert len(result) == 1
        assert result[0].titulo == "Casa"
        assert isinstance(result[0], Auction)