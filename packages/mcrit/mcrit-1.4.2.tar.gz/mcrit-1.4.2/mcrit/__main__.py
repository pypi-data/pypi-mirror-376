import re
import os
import sys


def runWorker(profiling=False):
    from mcrit.Worker import Worker
    with Worker(profiling=profiling) as worker:
        worker.run()


def runSpawningWorker(profiling=False):
    from mcrit.SpawningWorker import SpawningWorker
    with SpawningWorker(profiling=profiling) as spawning_worker:
        spawning_worker.run()


def runSingleJobWorker(job_id, profiling=False):
    from mcrit.SingleJobWorker import SingleJobWorker
    with SingleJobWorker(job_id, profiling=profiling) as single_job_worker:
        single_job_worker.run()


def runServer(profiling=False, uses_gunicorn=False):
    import platform
    from waitress import serve
    from mcrit.server.wsgi import app
    from mcrit.config.GunicornConfig import GunicornConfig
    try:
        import gunicorn
        from gunicorn.app.base import BaseApplication
    except Exception:
        gunicorn = None

    class gunicornServer(BaseApplication):
        def __init__(self, app):
            self.app = app
            super().__init__()
        
        def load_config(self):
            for key, value in GunicornConfig().toDict().items():
                try:
                    self.cfg.set(key.lower(), value)
                except AttributeError:
                    continue

        def load(self):
            return self.app

    wrapped_app = app
    if profiling:
        print("[!] Running as profiled application.")
        from werkzeug.middleware.profiler import ProfilerMiddleware
        profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profiler")
        os.makedirs(profile_dir, exist_ok=True)
        wrapped_app = ProfilerMiddleware(
            wrapped_app,
            restrictions=[30],
            profile_dir=profile_dir,
            filename_format="{method}-{path}-{time:.0f}-{elapsed:.0f}ms.prof",
        )
    
    platform = platform.system().lower()
    if platform == "linux" and gunicorn is not None and (GunicornConfig().USE_GUNICORN or uses_gunicorn):
        print("[!] Detected linux platform and gunicorn availability. Using gunicorn deployment.")
        gunicornServer(wrapped_app).run()
        sys.exit()
    elif platform == "windows":
        print("[!] Detected windows platform. Using waitress deployment.")
    else:
        print("[!] Could not determine platform, gunicorn not available or activated. Defaulting to waitress deployment.")
    # TODO consider allowing an argument to pass an configuration for initial setup of the instance
    serve(wrapped_app, listen="*:8000")


def runClient():
    from mcrit.client.McritConsole import McritConsole
    # we will re-parse arguments with more detail in McritConsole to keep this file concise
    console_client = McritConsole()
    console_client.run()


def main():
    # do not use argparse for processing here to allow using argparse help for the more intricate things in McritConsole
    if len(sys.argv) >= 2:
        is_profiling = False
        uses_gunicorn = False
        if len(sys.argv) >= 3 and "--profile" in sys.argv[2:]:
            is_profiling = True
        if len(sys.argv) >= 3 and "--gunicorn" in sys.argv[2:]:
            uses_gunicorn = True
        if sys.argv[1] == "server":
            runServer(profiling=is_profiling, uses_gunicorn=uses_gunicorn)
        elif sys.argv[1] == "worker":
            runWorker(profiling=is_profiling)
        elif sys.argv[1] == "spawningworker":
            runSpawningWorker(profiling=is_profiling)
        elif sys.argv[1] == "singlejobworker":
            # parse job_id directly from full command line string
            job_id = None
            match = re.search("--job_id (?P<job_id>[0-9a-fA-F]{24})", " ".join(sys.argv))
            if match:
                job_id = match.group("job_id")
                runSingleJobWorker(job_id, profiling=is_profiling)
            else:
                print("Was not able to recognize a job_id (24char hex string), did you pass it using --job_id?")
        elif sys.argv[1] == "client":
            runClient()
        else:
            print("Unrecognized command, please use {{server, worker, spawningworker, client}}")
    else:
        print(f"Usage: {sys.argv[0]} {{server, worker, spawningworker, client}}")
        print("Optionally use --profiling for {server, worker, spawningworker}")
        sys.exit()

if __name__ == "__main__":
    main()
