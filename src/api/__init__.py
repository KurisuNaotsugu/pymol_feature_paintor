# src/api/__init__.py
"""外部 API クライアント（AlphaFold DB, UniProt, etc.）"""

# module import
from api.alphafold import AlphaFoldApiConfig, AlphaFoldDBFetcherClient, AlphafoldApiClient
from api.pipeline import AccessionApiResponses, fetch_accession_api_responses
from api.uniprot import UniprotApiClients, UniprotApiConfig

# export symbols
__all__ = [
    "AlphafoldApiClient",
    "AlphaFoldApiConfig",
    "AlphaFoldDBFetcherClient",
    "UniprotApiClients",
    "UniprotApiConfig",
    "AccessionApiResponses",
    "fetch_accession_api_responses",
]
