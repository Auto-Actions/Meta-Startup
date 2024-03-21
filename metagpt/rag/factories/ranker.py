"""RAG Ranker Factory."""

from llama_index.core.llms import LLM
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.postprocessor.colbert_rerank import ColbertRerank

from metagpt.rag.factories.base import ConfigBasedFactory
from metagpt.rag.schema import BaseRankerConfig, ColbertRerankConfig, LLMRankerConfig


class RankerFactory(ConfigBasedFactory):
    """Modify creators for dynamically instance implementation."""

    def __init__(self):
        creators = {LLMRankerConfig: self._create_llm_ranker, ColbertRerankConfig: self._create_colbert_ranker}
        super().__init__(creators)

    def get_rankers(self, configs: list[BaseRankerConfig] = None, **kwargs) -> list[BaseNodePostprocessor]:
        """Creates and returns a retriever instance based on the provided configurations."""
        if not configs:
            return []

        return super().get_instances(configs, **kwargs)

    def _create_llm_ranker(self, config: LLMRankerConfig, **kwargs) -> LLMRerank:
        config.llm = self._extract_llm(config, **kwargs)
        return LLMRerank(**config.model_dump())

    def _create_colbert_ranker(self, config: ColbertRerankConfig, **kwargs) -> LLMRerank:
        return ColbertRerank(**config.model_dump())

    def _extract_llm(self, config: BaseRankerConfig = None, **kwargs) -> LLM:
        return self._val_from_config_or_kwargs("llm", config, **kwargs)


get_rankers = RankerFactory().get_rankers
