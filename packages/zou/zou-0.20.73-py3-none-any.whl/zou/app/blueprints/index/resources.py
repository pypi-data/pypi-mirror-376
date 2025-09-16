import psutil
import redis
import requests
import datetime

from flask import Response, abort
from flask_restful import Resource
from zou import __version__

from zou.app import app, config
from zou.app.utils import permissions, shell, date_helpers
from zou.app.services import projects_service, stats_service, persons_service
from flask_jwt_extended import jwt_required
from zou.app.utils.redis import get_redis_url


class IndexResource(Resource):
    def get(self):
        """
        Get API name and version.
        ---
        tags:
          - Index
        responses:
            200:
                description: API name and version
        """
        return {"api": config.APP_NAME, "version": __version__}


class BaseStatusResource(Resource):
    def get_status(self):
        is_db_up = True
        try:
            projects_service.get_or_create_status("Open")
        except Exception:
            is_db_up = False

        is_kv_up = True
        try:
            store = redis.StrictRedis(
                host=config.KEY_VALUE_STORE["host"],
                port=config.KEY_VALUE_STORE["port"],
                db=config.AUTH_TOKEN_BLACKLIST_KV_INDEX,
                password=config.KEY_VALUE_STORE["password"],
                decode_responses=True,
            )
            store.get("test")
        except redis.ConnectionError:
            is_kv_up = False

        is_es_up = True
        try:
            requests.get(
                f"http://{config.EVENT_STREAM_HOST}:{config.EVENT_STREAM_PORT}"
            )
        except Exception:
            is_es_up = False

        is_jq_up = True
        try:
            args = [
                "rq",
                "info",
                "--url",
                get_redis_url(config.KV_JOB_DB_INDEX),
            ]
            out = shell.run_command(args)
            is_jq_up = b"0 workers" not in out
        except Exception:
            app.logger.error("Job queue is not accessible", exc_info=1)
            is_jq_up = False

        is_indexer_up = True
        try:
            requests.get(
                f"{config.INDEXER['protocol']}://{config.INDEXER['host']}:{config.INDEXER['port']}"
            )
        except Exception:
            is_indexer_up = False

        version = __version__

        return (
            config.APP_NAME,
            version,
            is_db_up,
            is_kv_up,
            is_es_up,
            is_jq_up,
            is_indexer_up,
        )


class StatusResource(BaseStatusResource):
    def get(self):
        """
        Retrieve API name, version and status.
        ---
        tags:
          - Index
        responses:
            200:
                description: API name, version and status
        """
        (
            api_name,
            version,
            is_db_up,
            is_kv_up,
            is_es_up,
            is_jq_up,
            is_indexer_up,
        ) = self.get_status()

        return {
            "name": api_name,
            "version": version,
            "database-up": is_db_up,
            "key-value-store-up": is_kv_up,
            "event-stream-up": is_es_up,
            "job-queue-up": is_jq_up,
            "indexer-up": is_indexer_up,
        }


class StatusResourcesResource(BaseStatusResource):
    def get(self):
        """
        Retrieve date and CPU, memory and jobs stats.
        ---
        tags:
          - Index
        responses:
            200:
                description: Date and CPU, memory and jobs stats
        """
        loadavg = list(psutil.getloadavg())

        cpu_stats = {
            "percent": psutil.cpu_percent(interval=1, percpu=True),
            "loadavg": {
                "last 1 min": loadavg[0],
                "last 5 min": loadavg[1],
                "last 10 min": loadavg[2],
            },
        }

        memory_stats = {
            "total": psutil.virtual_memory().total,
            "used": psutil.virtual_memory().used,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
        }

        nb_jobs = 0
        if config.ENABLE_JOB_QUEUE:
            from zou.app.stores.queue_store import job_queue

            registry = job_queue.started_job_registry
            nb_jobs = registry.count
        job_stats = {
            "running_jobs": nb_jobs,
        }

        return {
            "date": datetime.datetime.now().isoformat(),
            "cpu": cpu_stats,
            "memory": memory_stats,
            "jobs": job_stats,
        }


class TxtStatusResource(BaseStatusResource):
    def get(self):
        """
        Retrieve API name, version and status as txt.
        ---
        tags:
          - Index
        responses:
            200:
                description: API name, version and status as txt
        """
        (
            api_name,
            version,
            is_db_up,
            is_kv_up,
            is_es_up,
            is_jq_up,
            is_indexer_up,
        ) = self.get_status()

        text = """name: %s
version: %s
database-up: %s
event-stream-up: %s
key-value-store-up: %s
job-queue-up: %s
indexer-up: %s
""" % (
            api_name,
            version,
            "up" if is_db_up else "down",
            "up" if is_kv_up else "down",
            "up" if is_es_up else "down",
            "up" if is_jq_up else "down",
            "up" if is_indexer_up else "down",
        )
        return Response(text, mimetype="text")


class InfluxStatusResource(BaseStatusResource):
    def get(self):
        """
        Retrieve status of database and time.
        ---
        tags:
          - Index
        responses:
            200:
                description: Status of database, key value, event stream, job queue and time
        """
        (
            _,
            _,
            is_db_up,
            is_kv_up,
            is_es_up,
            is_jq_up,
            is_indexer_up,
        ) = self.get_status()

        return {
            "database-up": int(is_db_up),
            "key-value-store-up": int(is_kv_up),
            "event-stream-up": int(is_es_up),
            "job-queue-up": int(is_jq_up),
            "indexer-up": int(is_indexer_up),
            "time": datetime.datetime.timestamp(
                date_helpers.get_utc_now_datetime()
            ),
        }


class StatsResource(Resource):
    @jwt_required()
    def get(self):
        """
        Retrieve main stats.
        ---
        tags:
          - Index
        responses:
            403:
                description: Permission denied
            200:
                description: Main stats
        """
        if not permissions.has_admin_permissions():
            abort(403)
        return stats_service.get_main_stats()


class ConfigResource(Resource):
    def get(self):
        """
        Get basic configuration for the current instance.
        ---
        tags:
          - Index
        responses:
            200:
                description: Configuration object including self-hosted status,
                    Crisp token, indexer configuration, SAML status, and dark
                    theme status.
        """
        organisation = persons_service.get_organisation()
        conf = {
            "is_self_hosted": config.IS_SELF_HOSTED,
            "crisp_token": config.CRISP_TOKEN,
            "dark_theme_by_default": organisation["dark_theme_by_default"],
            "indexer_configured": config.INDEXER["key"] is not None,
            "saml_enabled": config.SAML_ENABLED,
            "saml_idp_name": config.SAML_IDP_NAME,
            "default_locale": config.DEFAULT_LOCALE,
            "default_timezone": config.DEFAULT_TIMEZONE,
        }
        if config.SENTRY_KITSU_ENABLED:
            conf["sentry"] = {
                "dsn": config.SENTRY_KITSU_DSN,
                "sampleRate": config.SENTRY_KITSU_SR,
            }
        return conf


class TestEventsResource(Resource):
    def get(self):
        """
        Generate a main:test event.
        ---
        tags:
          - Index
        responses:
            200:
                description: Success flage
        """
        from zou.app.utils import events

        events.emit("main:test", data={}, persist=False, project_id=None)
        return {"success": True}
