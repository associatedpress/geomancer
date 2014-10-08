from geomancer.worker import queue_daemon
from geomancer import create_app

app = create_app()

queue_daemon(app)
