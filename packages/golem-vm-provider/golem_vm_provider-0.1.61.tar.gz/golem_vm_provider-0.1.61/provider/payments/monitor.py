import asyncio
from typing import Optional

from ..utils.logging import setup_logger
from ..vm.models import VMNotFoundError

logger = setup_logger(__name__)


class StreamMonitor:
    def __init__(self, *, stream_map, vm_service, reader, client, settings):
        self.stream_map = stream_map
        self.vm_service = vm_service
        self.reader = reader
        self.client = client
        self.settings = settings
        self._task: Optional[asyncio.Task] = None

    def _get(self, key: str, default=None):
        """Safely read setting from either an object with attributes or a dict-like mapping."""
        try:
            return getattr(self.settings, key)
        except Exception:
            try:
                return self.settings.get(key, default)
            except Exception:
                return default

    def start(self):
        if self._get("STREAM_MONITOR_ENABLED", False) or self._get("STREAM_WITHDRAW_ENABLED", False):
            logger.info(
                f"⏱️ Stream monitor enabled (check={self._get('STREAM_MONITOR_ENABLED', False)}, "
                f"withdraw={self._get('STREAM_WITHDRAW_ENABLED', False)}) interval={self._get('STREAM_MONITOR_INTERVAL_SECONDS', 60)}s"
            )
            self._task = asyncio.create_task(self._run(), name="stream-monitor")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self):
        last_withdraw = 0
        while True:
            try:
                await asyncio.sleep(int(self._get("STREAM_MONITOR_INTERVAL_SECONDS", 60)))
                items = await self.stream_map.all_items()
                now = int(self.reader.web3.eth.get_block("latest")["timestamp"]) if items else 0
                logger.debug(f"stream monitor tick: {len(items)} streams, now={now}")
                for vm_id, stream_id in items.items():
                    try:
                        s = self.reader.get_stream(stream_id)
                    except Exception as e:
                        # No payment info available; delete the VM and remove mapping per unified policy
                        logger.info(
                            f"Deleting VM {vm_id} due to missing/unavailable payment stream (id={stream_id}): {e}"
                        )
                        try:
                            await self.vm_service.delete_vm(vm_id)
                        except Exception as del_err:
                            logger.warning(f"delete_vm failed for {vm_id} after stream lookup failure: {del_err}")
                        try:
                            await self.stream_map.remove(vm_id)
                        except Exception as rem_err:
                            logger.debug(f"failed to remove vm {vm_id} from stream map: {rem_err}")
                        continue
                    # Stop VM if remaining runway < threshold
                    remaining = max(int(s["stopTime"]) - int(now), 0)
                    logger.debug(
                        f"stream {stream_id} for VM {vm_id}: start={s['startTime']} stop={s['stopTime']} "
                        f"rate={s['ratePerSecond']} withdrawn={s['withdrawn']} halted={s['halted']} remaining={remaining}s"
                    )
                    # If stream is force-halted, delete immediately to free all resources
                    if bool(s.get("halted")):
                        logger.info(
                            f"Deleting VM {vm_id} due to halted stream (id={stream_id}, now={now})"
                        )
                        try:
                            await self.vm_service.delete_vm(vm_id)
                            # Best-effort verification of deletion for investigation
                            try:
                                _ = await self.vm_service.get_vm_status(vm_id)
                                logger.info(
                                    f"Post-delete status check: VM {vm_id} still present after delete request"
                                )
                            except VMNotFoundError:
                                logger.info(
                                    f"Post-delete status check: VM {vm_id} not found (expected)"
                                )
                            except Exception as chk_err:
                                logger.debug(
                                    f"Post-delete status check failed for {vm_id}: {chk_err}"
                                )
                        except Exception as e:
                            logger.warning(f"delete_vm failed for {vm_id}: {e}")
                        try:
                            await self.stream_map.remove(vm_id)
                            logger.debug(f"Removed {vm_id} from stream map after delete")
                        except Exception as e:
                            logger.debug(f"failed to remove vm {vm_id} from stream map: {e}")
                        continue

                    # If runway is exhausted, delete the VM and remove mapping
                    if remaining == 0:
                        logger.info(
                            f"Deleting VM {vm_id} as stream runway is exhausted (id={stream_id}, now={now}, stop={s.get('stopTime')})"
                        )
                        # Capture pre-delete status for context
                        try:
                            pre = await self.vm_service.get_vm_status(vm_id)
                            logger.info(
                                f"Pre-delete status for {vm_id}: status={getattr(pre, 'status', '?')} ip={getattr(pre, 'ip_address', '?')}"
                            )
                        except VMNotFoundError:
                            logger.info(
                                f"Pre-delete status for {vm_id}: not found (will remove mapping)"
                            )
                        except Exception as pre_err:
                            logger.debug(f"Pre-delete status check failed for {vm_id}: {pre_err}")

                        try:
                            await self.vm_service.delete_vm(vm_id)
                            # Verify deletion
                            try:
                                _ = await self.vm_service.get_vm_status(vm_id)
                                logger.info(
                                    f"Post-delete status check: VM {vm_id} still present after delete request"
                                )
                            except VMNotFoundError:
                                logger.info(
                                    f"Post-delete status check: VM {vm_id} not found (expected)"
                                )
                            except Exception as chk_err:
                                logger.debug(
                                    f"Post-delete status check failed for {vm_id}: {chk_err}"
                                )
                        except Exception as e:
                            logger.warning(f"delete_vm failed for {vm_id}: {e}")
                        try:
                            await self.stream_map.remove(vm_id)
                            logger.info(f"Removed mapping for {vm_id} after delete on exhausted runway")
                        except Exception as rem_err:
                            logger.debug(
                                f"failed to remove vm {vm_id} from stream map after delete: {rem_err}"
                            )
                        continue

                    # Otherwise, do not stop; just log health and consider withdrawals
                    logger.debug(
                        f"VM {vm_id} stream {stream_id} healthy (remaining={remaining}s)"
                    )
                    # Withdraw if enough vested and configured
                    if self._get("STREAM_WITHDRAW_ENABLED", False) and self.client:
                        vested = max(min(now, s["stopTime"]) - s["startTime"], 0) * s["ratePerSecond"]
                        withdrawable = max(vested - s["withdrawn"], 0)
                        logger.debug(f"withdraw check stream {stream_id}: vested={vested} withdrawable={withdrawable}")
                        # Enforce a minimum interval between withdrawals
                        if withdrawable >= int(self._get("STREAM_MIN_WITHDRAW_WEI", 0)) and (
                            now - last_withdraw >= int(self._get("STREAM_WITHDRAW_INTERVAL_SECONDS", 1800))
                        ):
                            try:
                                self.client.withdraw(stream_id)
                                last_withdraw = now
                            except Exception as e:
                                logger.warning(f"withdraw failed for {stream_id}: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"stream monitor error: {e}")
