from .libfec_client import LibfecClient, RssWatcherState, ExportState

# Shared state - singleton instances
libfec_client = LibfecClient()
rss_watcher_state = RssWatcherState()
export_state = ExportState()
