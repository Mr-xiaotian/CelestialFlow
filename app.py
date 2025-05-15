from flask import Flask, render_template, jsonify, request
from datetime import datetime
import random

app = Flask(__name__)

# 初始化任务状态
node_statuses = {
    "RootStage": {
        "active": True,
        "tasks_processed": 0,
        "tasks_pending": 100,
        "tasks_error": 0,
        "start_time": datetime.now().isoformat(),
        "execution_mode": "thread",
        "stage_mode": "process",
        "func_name": "process_task"
    },
    "Splitter": {
        "active": True,
        "tasks_processed": 0,
        "tasks_pending": 0,
        "tasks_error": 0,
        "start_time": datetime.now().isoformat(),
        "execution_mode": "thread",
        "stage_mode": "process",
        "func_name": "split_task"
    },
    "Processor": {
        "active": True,
        "tasks_processed": 0,
        "tasks_pending": 0,
        "tasks_error": 0,
        "start_time": datetime.now().isoformat(),
        "execution_mode": "thread",
        "stage_mode": "process",
        "func_name": "process_item"
    },
    "Validator": {
        "active": True,
        "tasks_processed": 0,
        "tasks_pending": 0,
        "tasks_error": 0,
        "start_time": datetime.now().isoformat(),
        "execution_mode": "thread",
        "stage_mode": "process",
        "func_name": "validate_item"
    }
}

errors = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def get_status():
    return jsonify({
        "nodes": node_statuses,
        "errors": errors
    })

@app.route("/start", methods=["POST"])
def start_simulation():
    return jsonify({"status": "started"})

@app.route("/stop", methods=["POST"])
def stop_simulation():
    return jsonify({"status": "stopped"})

@app.route("/reset", methods=["POST"])
def reset_simulation():
    for name, node in node_statuses.items():
        node.update({
            "active": True,
            "tasks_processed": 0,
            "tasks_pending": 100 if name == "RootStage" else 0,
            "tasks_error": 0,
            "start_time": datetime.now().isoformat()
        })
    errors.clear()
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    app.run(debug=True)
