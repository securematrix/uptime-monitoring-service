import os
import logging
from flask import Flask, request, jsonify, render_template
from database import init_db, get_db_session
from models import Monitor, MonitorLog
from scheduler import start_scheduler
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

init_db()
start_scheduler()

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/monitors', methods=['GET'])
def get_monitors():
    db = get_db_session()
    try:
        monitors = db.query(Monitor).all()
        res = []
        for m in monitors:
            total_logs = db.query(MonitorLog).filter(MonitorLog.monitor_id == m.id).count()
            success_logs = db.query(MonitorLog).filter(MonitorLog.monitor_id == m.id, MonitorLog.is_success == True).count()
            uptime = (success_logs / total_logs * 100) if total_logs > 0 else 100.0
            
            res.append({
                "id": m.id,
                "name": m.name,
                "url": m.url,
                "method": m.method,
                "frequency": m.frequency,
                "is_paused": m.is_paused,
                "uptime_percent": round(uptime, 2)
            })
        return jsonify(res)
    finally:
        db.close()

@app.route('/api/monitors', methods=['POST'])
def add_monitor():
    data = request.json
    db = get_db_session()
    try:
        new_monitor = Monitor(
            name=data.get('name'),
            url=data.get('url'),
            method=data.get('method', 'GET').upper(),
            frequency=int(data.get('frequency', 60)),
            timeout=float(data.get('timeout', 10.0)),
            alert_email=data.get('alert_email'),
            alert_webhook=data.get('alert_webhook')
        )
        db.add(new_monitor)
        db.commit()
        return jsonify({"success": True, "id": new_monitor.id})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()

@app.route('/api/monitors/<int:monitor_id>/logs', methods=['GET'])
def get_monitor_logs(monitor_id):
    db = get_db_session()
    try:
        logs = db.query(MonitorLog).filter(MonitorLog.monitor_id == monitor_id)\
                 .order_by(MonitorLog.timestamp.desc()).limit(100).all()
        res = []
        for log in logs:
            res.append({
                "timestamp": log.timestamp.isoformat(),
                "status_code": log.status_code,
                "response_time": log.response_time,
                "is_success": log.is_success,
                "error_message": log.error_message
            })
        return jsonify(res)
    finally:
        db.close()

@app.route('/api/monitors/<int:monitor_id>/stats', methods=['GET'])
def get_monitor_stats(monitor_id):
    db = get_db_session()
    try:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        logs = db.query(MonitorLog).filter(MonitorLog.monitor_id == monitor_id, MonitorLog.timestamp >= time_threshold).all()
        
        total = len(logs)
        success = sum(1 for l in logs if l.is_success)
        uptime = (success / total * 100) if total > 0 else 100.0
        avg_resp = sum((l.response_time for l in logs if l.response_time), 0.0) / success if success > 0 else 0.0
        
        return jsonify({
            "uptime_24h": round(uptime, 2),
            "avg_response_time_ms": round(avg_resp, 2),
            "total_checks_24h": total,
            "downtime_incidents": total - success
        })
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
