import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import httpx

from elephantine.storage.sqlite_store import SqliteMetadataStore

logger = logging.getLogger(__name__)

WEEKDAY_MAP = {
    'MON': 0, 'MONDAY': 0,
    'TUE': 1, 'TUESDAY': 1,
    'WED': 2, 'WEDNESDAY': 2,
    'THU': 3, 'THURSDAY': 3,
    'FRI': 4, 'FRIDAY': 4,
    'SAT': 5, 'SATURDAY': 5,
    'SUN': 6, 'SUNDAY': 6
}

def parse_trigger_condition(
    trigger_type: str,
    condition_value: str,
    reference_time: Optional[datetime] = None
) -> Tuple[datetime, bool]:
    now = reference_time or datetime.now(timezone.utc)
    condition = condition_value.strip()

    if trigger_type == 'datetime' or not condition.startswith(('every:', 'weekly:', 'daily:')):
        try:
            dt = datetime.fromisoformat(condition.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt, False
        except Exception:
            pass

    if condition.startswith('every:'):
        val_str = condition[6:].strip().lower()
        if val_str.endswith('s'):
            secs = int(val_str[:-1])
        elif val_str.endswith('m'):
            secs = int(val_str[:-1]) * 60
        elif val_str.endswith('h'):
            secs = int(val_str[:-1]) * 3600
        elif val_str.endswith('d'):
            secs = int(val_str[:-1]) * 86400
        else:
            secs = int(val_str)
        return now + timedelta(seconds=secs), True

    if condition.startswith('daily:'):
        time_part = condition[6:].strip()
        hour, minute = map(int, time_part.split(':'))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target, True

    if condition.startswith('weekly:'):
        parts = condition[7:].strip().split(':')
        day_str = parts[0].upper()
        hour = int(parts[1]) if len(parts) > 1 else 9
        minute = int(parts[2]) if len(parts) > 2 else 0

        target_weekday = WEEKDAY_MAP.get(day_str, 4)
        days_ahead = target_weekday - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and now.time() >= datetime.min.time().replace(hour=hour, minute=minute)):
            days_ahead += 7

        target = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        return target, True

    return now + timedelta(hours=1), False


class ProactiveEngine:
    def __init__(self, sqlite_store: SqliteMetadataStore, check_interval_seconds: float = 15.0):
        self.sqlite_store = sqlite_store
        self.check_interval_seconds = check_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._listeners: List[asyncio.Queue] = []

    def subscribe_listener(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._listeners.append(q)
        return q

    def unsubscribe_listener(self, q: asyncio.Queue) -> None:
        if q in self._listeners:
            self._listeners.remove(q)

    async def broadcast_alert(self, alert_data: Dict[str, Any]) -> None:
        for q in list(self._listeners):
            try:
                await q.put(alert_data)
            except Exception:
                pass

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_evaluator_loop())
        logger.info('ProactiveEngine background daemon started.')

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info('ProactiveEngine background daemon stopped.')

    async def _run_evaluator_loop(self) -> None:
        while self._running:
            try:
                await self.evaluate_due_triggers()
            except Exception as e:
                logger.error(f'Error during proactive triggers evaluation: {e}')
            await asyncio.sleep(self.check_interval_seconds)

    async def evaluate_due_triggers(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        now = current_time or datetime.now(timezone.utc)
        due_triggers = await self.sqlite_store.get_due_proactive_triggers(now)
        fired_alerts = []

        for trigger in due_triggers:
            t_id = trigger['id']
            c_val = trigger['condition_value']
            t_type = trigger['trigger_type']
            webhook = trigger.get('webhook_url')

            _, is_recurring = parse_trigger_condition(t_type, c_val, reference_time=now)
            next_run = None
            if is_recurring:
                next_run, _ = parse_trigger_condition(t_type, c_val, reference_time=now)

            alert_id = await self.sqlite_store.mark_trigger_fired(
                trigger_id=t_id,
                memory_id=trigger["memory_id"],
                target_agent=trigger["target_agent"],
                workspace_id=trigger["workspace_id"],
                next_trigger_at=next_run,
                is_recurring=is_recurring
            )

            alert_payload = {
                'trigger_id': t_id,
                'memory_id': trigger['memory_id'],
                'content': trigger['memory_content'],
                'category': trigger.get('memory_category', 'general'),
                'workspace_id': trigger['workspace_id'],
                'target_agent': trigger['target_agent'],
                'role_authority': trigger.get('role_authority', 0.5),
                'condition': c_val,
                'triggered_at': now.isoformat(),
                'is_recurring': is_recurring,
                'next_trigger_at': next_run.isoformat() if next_run else None
            }
            fired_alerts.append(alert_payload)

            await self.broadcast_alert(alert_payload)

            if webhook:
                asyncio.create_task(self._dispatch_webhook(webhook, alert_payload))

        return fired_alerts

    async def _dispatch_webhook(self, url: str, payload: Dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.warning(f'Webhook dispatch failed for {url}: {e}')
