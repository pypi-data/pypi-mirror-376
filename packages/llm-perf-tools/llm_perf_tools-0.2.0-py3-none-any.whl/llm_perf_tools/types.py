from pydantic import BaseModel


class RequestMetrics(BaseModel):
    request_start: float
    first_token_time: float | None = None
    request_end: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    ttft: float | None = None
    e2e_latency: float | None = None
    itl: float | None = None
    tps: float | None = None
    prefill_time: float | None = None
    decode_time: float | None = None


class InferenceStats(BaseModel):
    ttft: float | None = None
    e2e_latency: float | None = None
    itl: float | None = None
    tps: float | None = None


class BatchInferenceStats(BaseModel):
    # Time to First Token
    avg_ttft: float | None = None
    p50_ttft: float | None = None
    p95_ttft: float | None = None
    p99_ttft: float | None = None
    min_ttft: float | None = None
    max_ttft: float | None = None

    # End-to-End Latency
    avg_e2e_latency: float | None = None
    p50_e2e_latency: float | None = None
    p95_e2e_latency: float | None = None
    p99_e2e_latency: float | None = None
    min_e2e_latency: float | None = None
    max_e2e_latency: float | None = None

    # Inter-token Latency
    avg_itl: float | None = None
    p50_itl: float | None = None
    p95_itl: float | None = None
    p99_itl: float | None = None
    min_itl: float | None = None
    max_itl: float | None = None

    # Tokens Per Second
    avg_tps: float | None = None
    p50_tps: float | None = None
    p5_tps: float | None = None
    p1_tps: float | None = None
    min_tps: float | None = None
    max_tps: float | None = None
    overall_tps: float | None = None

    # Token Counts
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_input_tokens: float | None = None
    avg_output_tokens: float | None = None

    # Requests Per Second
    rps: float | None = None

    total_requests: int = 0
    successful_requests: int = 0


class GPUMetrics(BaseModel):
    timestamp: float
    gpu_id: int
    memory_used_mb: int
    memory_total_mb: int
    memory_utilization_percent: float
    gpu_utilization_percent: int
    temperature_celsius: int
    power_draw_watts: float
