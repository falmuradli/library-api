from flask import Blueprint, jsonify

from services import reportService as reports

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("/reports/overdue")
def report_overdue():
    return jsonify(reports.overdue_report())


@reports_bp.get("/reports/summary")
def report_summary():
    return jsonify(reports.summary_report())
