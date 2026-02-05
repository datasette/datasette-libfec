from .libfec_client import LibfecClient, ExportState

# Shared state - singleton instances
libfec_client = LibfecClient()
export_state = ExportState()
