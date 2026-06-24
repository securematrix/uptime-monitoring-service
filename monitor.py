import asyncio
import aiohttp
import time
from datetime import datetime, timezone
import logging
from database import get_db_session
from models import Monitor, MonitorLog
from alerts import send_alert
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def fetch(url, method, timeout_seconds):
    try:
        start_time = time.perf_counter()
        
        ttfb = None
        
        async def on_request_chunk_sent(session, trace_config_ctx, params):
            trace_config_ctx.start = time.perf_counter()

        async def on_response_chunk_received(session, trace_config_ctx, params):
            nonlocal ttfb
            if ttfb is None:
                ttfb = (time.perf_counter() - trace_config_ctx.start) * 1000

        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_chunk_sent.append(on_request_chunk_sent)
        trace_config.on_response_chunk_received.append(on_response_chunk_received)
        
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        
        async with aiohttp.ClientSession(timeout=timeout, trace_configs=[trace_config]) as local_session:
            if method.upper() == 'HEAD':
                req = local_session.head(url, allow_redirects=True)
            else:
                req = local_session.get(url, allow_redirects=True)
                
            async with req as response:
                if method.upper() == 'GET':
                    await response.read()
                
                total_time = (time.perf_counter() - start_time) * 1000
                
                if ttfb is None:
                    ttfb = total_time
                    
                is_success = 200 <= response.status < 400
                return {
                    'status_code': response.status,
                    'response_time': total_time,
                    'ttfb': ttfb,
                    'is_success': is_success,
                    'error_message': None
                }
    except asyncio.TimeoutError:
        return {
            'status_code': None,
            'response_time': timeout_seconds * 1000,
            'ttfb': None,
            'is_success': False,
            'error_message': 'Connection Timeout'
        }
    except Exception as e:
        return {
            'status_code': None,
            'response_time': None,
            'ttfb': None,
            'is_success': False,
            'error_message': str(e)[:200]
        }


async def check_monitor(monitor_id):
    db = get_db_session()
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        if not monitor or monitor.is_paused:
            return

        logger.info(f"Checking monitor {monitor.name} ({monitor.url})")
        
        result = await fetch(monitor.url, monitor.method, monitor.timeout)
        
        log = MonitorLog(
            monitor_id=monitor.id,
            timestamp=datetime.now(timezone.utc),
            status_code=result['status_code'],
            response_time=result['response_time'],
            ttfb=result['ttfb'],
            is_success=result['is_success'],
            error_message=result['error_message']
        )
        db.add(log)
        db.commit()
        
        await check_alerts(db, monitor, log)
        
    except Exception as e:
        logger.error(f"Error checking monitor {monitor_id}: {e}")
    finally:
        db.close()

async def check_alerts(db, monitor, latest_log):
    if not latest_log.is_success:
        recent_logs = db.query(MonitorLog).filter(MonitorLog.monitor_id == monitor.id)\
            .order_by(MonitorLog.timestamp.desc())\
            .limit(monitor.alert_threshold_consecutive_drops).all()
        
        if len(recent_logs) == monitor.alert_threshold_consecutive_drops:
            if all(not log.is_success for log in recent_logs):
                send_alert(monitor, f"Service is down. Error: {latest_log.error_message}")
    elif latest_log.response_time and latest_log.response_time > monitor.alert_response_time_threshold:
        send_alert(monitor, f"High response time: {latest_log.response_time:.2f}ms exceeds threshold {monitor.alert_response_time_threshold}ms")
