import threading
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

console = Console()

class TelemetryDashboard:
    """可观测性与成本测算大盘（线程安全单例模式）"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(TelemetryDashboard, cls).__new__(cls)
                cls._instance.total_prompt_tokens = 0
                cls._instance.total_completion_tokens = 0
                cls._instance.success_count = 0
                cls._instance.failed_count = 0
                # 参考常见开源模型（如 DeepSeek）的定价：输入 1元/百万Token，输出 2元/百万Token
                cls._instance.price_per_m_prompt = 1.0 
                cls._instance.price_per_m_comp = 2.0
        return cls._instance

    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

    def record_result(self, is_success: bool):
        if is_success:
            self.success_count += 1
        else:
            self.failed_count += 1

    def calculate_cost(self) -> float:
        cost = (self.total_prompt_tokens / 1_000_000 * self.price_per_m_prompt) + \
               (self.total_completion_tokens / 1_000_000 * self.price_per_m_comp)
        return round(cost, 4)

    def print_summary(self):
        """在终端渲染极其绚丽的统计面板"""
        total_tasks = self.success_count + self.failed_count
        success_rate = (self.success_count / total_tasks * 100) if total_tasks > 0 else 0
        
        summary_text = (
            f"[cyan]总处理语料数: [/cyan] {total_tasks} 条\n"
            f"[green]高质 SFT 合成成功: [/green] {self.success_count} 条\n"
            f"[red]被法官打回/清洗过滤: [/red] {self.failed_count} 条\n"
            f"[yellow]SFT 数据合格率: [/yellow] {success_rate:.2f}%\n"
            f"[magenta]累计消耗 Tokens: [/magenta] {self.total_prompt_tokens + self.total_completion_tokens:,}\n"
            f"[bold red]折合 API 账单成本:[/bold red] ¥{self.calculate_cost()} 元"
        )
        console.print(Panel(summary_text, title="🚀 Agent-SFT-Forge 熔炉执行报告", border_style="green"))
