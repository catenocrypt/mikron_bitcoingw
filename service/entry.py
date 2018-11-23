import api
import watcher_job
import config

from bottle import run
from threading import Thread

cfg = config.get_config()
watcher_thread = Thread(target=watcher_job.start_job)
watcher_thread.start()

listen_host = cfg['listen_host']
listen_port = cfg['listen_port']
run(host = listen_host, port = listen_port, debug = True)

print("stop")
watcher_thread.do_run = False
watcher_thread.join()

