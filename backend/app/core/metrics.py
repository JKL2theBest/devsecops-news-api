import os
from pathlib import Path

from prometheus_client import Counter

prometheus_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
if prometheus_dir:
    Path(prometheus_dir).mkdir(parents=True, exist_ok=True)

NEWS_CREATED_TOTAL = Counter("news_created_total", "Total number of news created")

USERS_REGISTERED_TOTAL = Counter("users_registered_total", "Total number of registered users")

NOTIFICATIONS_SENT_TOTAL = Counter("notifications_sent_total", "Total number of email notifications sent", ["type"])
