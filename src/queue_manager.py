# src/queue_manager.py
import os
import json
import time
import msvcrt
import logging
from datetime import datetime
from typing import Dict, Optional


class AlarmQueue:
    def __init__(self, queue_dir: str = 'queue'):
        self.queue_dir = queue_dir
        self.logger = logging.getLogger(__name__)

        # Ensure queue directory exists
        if not os.path.exists(queue_dir):
            os.makedirs(queue_dir)

        # Create lock file
        self.lock_file = os.path.join(queue_dir, 'queue.lock')
        if not os.path.exists(self.lock_file):
            open(self.lock_file, 'w').close()

    def _acquire_lock(self) -> bool:
        """Acquire file lock for queue operations."""
        try:
            self.lock_fd = open(self.lock_file, 'r+b')
            msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except (IOError, OSError) as e:
            self.logger.warning(f"Could not acquire lock: {e}")
            return False

    def _release_lock(self):
        """Release file lock."""
        try:
            msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
            self.lock_fd.close()
        except Exception as e:
            self.logger.error(f"Error releasing lock: {e}")

    def enqueue_alarm(self, alarm_description: str, group_id: int, is_special_day: bool = False) -> str:
        """
        Add alarm to queue with unique ID.

        Args:
            alarm_description: Description of the alarm
            group_id: Group ID to notify
            is_special_day: Flag indicating if this is a special day notification
        """
        alarm_id = f"alarm_{int(time.time() * 1000)}_{group_id}"
        alarm_data = {
            'id': alarm_id,
            'description': alarm_description.strip(),
            'group_id': group_id,
            'timestamp': datetime.now().isoformat(),
            'special_day': is_special_day,
            'status': 'pending'
        }

        if self._acquire_lock():
            try:
                queue_file = os.path.join(self.queue_dir, f"{alarm_id}.json")
                self.logger.info(f"Writing to file: {queue_file}")

                with open(queue_file, 'w') as f:
                    json.dump(alarm_data, f)

                self.logger.info(f"File written successfully: {queue_file}")
                return alarm_id
            except Exception as e:
                self.logger.error(f"Failed to write queue file: {e}")
                raise
            finally:
                self._release_lock()

    def get_next_alarm(self) -> Optional[Dict]:
        """Get next pending alarm from queue."""
        if self._acquire_lock():
            try:
                # Get oldest pending alarm
                pending_alarms = []
                for filename in os.listdir(self.queue_dir):
                    if not filename.endswith('.json'):
                        continue

                    filepath = os.path.join(self.queue_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            alarm_data = json.load(f)
                            if alarm_data['status'] == 'pending':
                                pending_alarms.append((alarm_data['timestamp'], alarm_data))
                    except json.JSONDecodeError:
                        self.logger.error(f"Corrupted alarm file: {filepath}")
                        continue

                if pending_alarms:
                    # Sort by timestamp and get oldest
                    pending_alarms.sort(key=lambda x: x[0])
                    return pending_alarms[0][1]
                return None
            finally:
                self._release_lock()
        return None

    def mark_completed(self, alarm_id: str):
        """Mark alarm as completed."""
        if self._acquire_lock():
            try:
                alarm_file = os.path.join(self.queue_dir, f"{alarm_id}.json")
                if os.path.exists(alarm_file):
                    with open(alarm_file, 'r') as f:
                        alarm_data = json.load(f)

                    alarm_data['status'] = 'completed'
                    alarm_data['completed_at'] = datetime.now().isoformat()

                    with open(alarm_file, 'w') as f:
                        json.dump(alarm_data, f)
            finally:
                self._release_lock()

    def mark_failed(self, alarm_id: str, error: str):
        """Mark alarm as failed with error message."""
        if self._acquire_lock():
            try:
                alarm_file = os.path.join(self.queue_dir, f"{alarm_id}.json")
                if os.path.exists(alarm_file):
                    with open(alarm_file, 'r') as f:
                        alarm_data = json.load(f)

                    alarm_data['status'] = 'failed'
                    alarm_data['error'] = error
                    alarm_data['failed_at'] = datetime.now().isoformat()

                    with open(alarm_file, 'w') as f:
                        json.dump(alarm_data, f)
            finally:
                self._release_lock()