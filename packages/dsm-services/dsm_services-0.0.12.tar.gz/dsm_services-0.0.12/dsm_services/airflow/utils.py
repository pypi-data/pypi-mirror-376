import json
from html import escape

def create_notice_email(site_name, context):
    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    execution_date = context['dag_run'].logical_date

    subject = f"Airflow {site_name} alert: {dag_id}.{task_id} failed"

    ti = context["task_instance"]

    try: 
        with open(f"/opt/airflow/logs/dag_id={ti.dag_id}/run_id={ti.run_id}/task_id={ti.task_id}/attempt={ti.try_number}.log", 'r') as f:
            log_lines = f.read()
    except Exception as e:
        log_lines = ""
    body = render_logs_to_html(site_name=site_name,dag_id=dag_id, task_id=task_id, exec_time=execution_date, log_lines=log_lines)

    return subject, body


def render_logs_to_html(
    site_name: str,
    dag_id: str,
    task_id: str,
    exec_time: str,
    log_lines: str, 
) -> str:
    """
    Convert JSON log lines into an HTML table with modern styling and
    DAG/Task/Execution metadata if available.
    """
    # Map log levels to colors
    level_colors = {
        "info": "#2196F3",      # Blue
        "warning": "#FFC107",   # Amber
        "error": "#F44336",     # Red
    }
    
    rows = []
    for line in log_lines.strip().splitlines():
        try:
            entry = json.loads(line)
            ts = entry.get("timestamp", "")
            level = entry.get("level", "").lower()
            event = entry.get("event", "")
            logger = entry.get("logger", "")

            # Escape text for safe HTML
            ts = escape(ts)
            event = escape(str(event))
            logger = escape(logger)
            
            color = level_colors.get(level, "#9E9E9E")  # Default grey
            
            row = f"""
            <tr>
                <td class="ts">{ts}</td>
                <td><span class="level" style="background:{color};">{level.upper()}</span></td>
                <td class="logger">{logger}</td>
                <td><pre class="event">{event}</pre></td>
            </tr>
            """
            rows.append(row)
        except json.JSONDecodeError:
            continue  # Skip non-JSON lines
    
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: "Segoe UI", Roboto, sans-serif;
                background: #1e1e1e;
                color: #ddd;
                margin: 20px;
            }}
            h1, h2, h3 {{
                margin: 6px 0;
            }}
            .meta-item {{
                margin: 4px 0;
                font-size: 14px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                background: #252526;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 6px rgba(0,0,0,0.5);
            }}
            th, td {{
                padding: 10px 12px;
                border-bottom: 1px solid #333;
                vertical-align: top;
            }}
            th {{
                background: #333;
                color: #fff;
                text-align: left;
            }}
            tr:hover {{
                background: #2d2d30;
            }}
            .ts {{
                color: #9CDCFE;
                white-space: nowrap;
            }}
            .level {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                color: #000;
            }}
            .logger {{
                color: #B5CEA8;
                font-size: 13px;
            }}
            .event {{
                margin: 0;
                white-space: pre-wrap;
                color: #ddd;
                font-family: monospace;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div>
            <h2>{escape(site_name)}</h2>
            {"<div class='meta-item'><strong>DAG:</strong> " + escape(dag_id) + "</div>" if dag_id else ""}
            {"<div class='meta-item'><strong>Task:</strong> " + escape(task_id) + "</div>" if task_id else ""}
            {"<div class='meta-item'><strong>Execution Time:</strong> " + escape(f"{exec_time}") + "</div>" if exec_time else ""}
        </div>
        
        <h2>Logs</h2>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Logger</th>
                <th>Event</th>
            </tr>
            {''.join(rows)}
        </table>
    </body>
    </html>
    """
    return html