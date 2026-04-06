from prometheus_client import Counter, Histogram, start_http_server

class Telemetry:
    """生产级监控：对接 Prometheus + Grafana"""
    def __init__(self, port=9091):
        self.task_counter = Counter('sft_task_total', '处理任务总数', ['status'])
        self.cost_gauge = Counter('llm_cost_usd', 'Token 累计消耗美元')
        start_http_server(port)

    def record_task(self, status):
        self.task_counter.labels(status=status).inc()

    def record_cost(self, amount):
        self.cost_gauge.inc(amount)

telemetry = Telemetry()