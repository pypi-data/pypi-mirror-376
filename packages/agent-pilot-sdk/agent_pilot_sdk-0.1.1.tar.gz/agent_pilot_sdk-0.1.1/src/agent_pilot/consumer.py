import time
import atexit
import logging
from threading import Thread
from typing import Optional, Any
from .config import get_config
from .models import TrackingEvent
from .http_client import get_http_client

logger = logging.getLogger(__name__)


DEFAULT_FLUSH_INTERVAL = 0.5


class Consumer:
    def __init__(self, event_queue: Any, api_key: Optional[str] = None) -> None:
        self.running = True
        self.event_queue = event_queue
        self.api_key = api_key
        self.http_client = get_http_client()

        self._thread = Thread(target=self.run, daemon=True)
        atexit.register(self._final_flush)

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def run(self) -> None:
        while self.running:
            self.send_batch()
            time.sleep(DEFAULT_FLUSH_INTERVAL)

        self.send_batch()

    def send_batch(self) -> None:
        config = get_config()
        batch: list[TrackingEvent] = self.event_queue.get_batch()

        verbose = config.verbose
        api_url = config.api_url
        workspace_id = config.workspace_id

        if len(batch) > 0:
            api_key = self.api_key or config.api_key
            if not api_key:
                logger.error("API key not found. Please provide an API key.")
                return

            if verbose:
                logger.info(f"Sending {len(batch)} events.")
                for event in batch:
                    event_data = event.model_dump(
                        exclude_none=True,
                        exclude_unset=True,
                        exclude_defaults=True,
                    )
                    logger.info(f"event {event.run_id}: {event_data}")

            try:
                if verbose:
                    logger.info(f"Sending events to {api_url}")

                task_id = batch[0].task_id
                data = {
                    "TaskId": task_id,
                    "workspace_id": workspace_id,
                    "TrackingEvents": [
                        event.model_dump(
                            exclude_none=True,
                            exclude_unset=True,
                            exclude_defaults=True,
                        )
                        for event in batch
                    ],
                }

                if verbose:
                    logger.info(f"Sending data: {data}")

                action = "TrackingEvent"
                response_data, response_status_code = self.http_client.post(
                    action=action, data=data, api_key=api_key, api_url=api_url
                )

                if verbose:
                    logger.info(
                        f"Events sent. response_data: {response_data}, response_status_code: {response_status_code}"
                    )
            except Exception as e:
                if verbose:
                    logger.exception(f"Error sending events: {e}", exc_info=True)
                else:
                    logger.error("Error sending events", exc_info=True)

                self.event_queue.append(batch)

    def _final_flush(self) -> None:
        if hasattr(self, "running"):
            self.running = False
        else:
            return
        try:
            if self.event_queue.len() > 0:
                self.send_batch()
        except Exception as e:
            logger.error(f"Error in final flush: {e}", exc_info=True)

    def stop(self) -> None:
        self.running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
