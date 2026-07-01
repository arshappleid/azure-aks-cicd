from datetime import datetime
from fastapi import FastAPI, APIRouter, Request
import os
import time
import logging

# --- OpenTelemetry Core Setup (Logs & Metrics) ---
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from opentelemetry.sdk.resources import Resource

def setup_splunk_telemetry():
    # Define a single resource identity for both logs and metrics
    resource = Resource.create({
        "service.name": "prabhmeets-fastapi-server",
        "deployment.environment": os.getenv("ENVIRONMENT", "prod")
    })
    
    # 1. Configure OpenTelemetry LOGS
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    otlp_log_exporter = OTLPLogExporter(endpoint=otel_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    
    # Attach to Python's native logging
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    
    # 2. Configure OpenTelemetry METRICS (Replaces Prometheus Server)
    otlp_metric_exporter = OTLPMetricExporter(endpoint=otel_endpoint, insecure=True)
    # Automatically read and push metrics to Splunk every 15-60 seconds asynchronously
    metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=15000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

# Initialize Telemetry
setup_splunk_telemetry()
logger = logging.getLogger("fastapi_app")
meter = metrics.get_meter("fastapi_meter")

# Define OTel Metrics (Replacing Prometheus Counter and Histogram)
request_counter = meter.create_counter(
    name="fastapi_requests_total",
    description="Total number of HTTP requests received"
)
request_latency_histogram = meter.create_histogram(
    name="fastapi_request_duration_seconds",
    description="HTTP request latency in seconds",
    unit="s"
)


# --- FastAPI Application ---
path_prefix = os.getenv("PATH_PREFIX", "")

app = FastAPI(
    title="Prabhmeets FastAPI Server",
    version="1.0.0",
    root_path=path_prefix,
)
router = APIRouter()

@router.get("/health")
def health_check():
    logger.info("Health check endpoint hit")
    return {"status": "healthy"}

@router.get("/info")
def hello_world():
    current_time = datetime.now().strftime("%I:%M %p")
    env = os.getenv("ENVIRONMENT", "Missing ENVIRONMENT variable")
    logger.info("Info endpoint metadata resolved", extra={"env": env})
    return {"message": "Prabhmeets Server", "time": current_time, "env": env}


# --- OTel Middleware (Capturing Metrics & Logs) ---
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    latency = time.time() - start_time
    endpoint = request.scope.get("route").path if request.scope.get("route") else request.url.path

    # Metric & Log Attributes (Labels)
    attributes = {
        "http.method": request.method,
        "http.route": endpoint,
        "http.status_code": str(response.status_code)
    }

    # 1. Record OpenTelemetry Metrics (Pushed automatically!)
    request_latency_histogram.record(latency, attributes=attributes)
    request_counter.add(1, attributes=attributes)
    
    # 2. Record OpenTelemetry Logs
    log_extra = {**attributes, "duration_ms": int(latency * 1000)}
    if response.status_code >= 400:
        logger.error(f"HTTP Request failed with status {response.status_code}", extra=log_extra)
    else:
        logger.info(f"HTTP Request processed successfully", extra=log_extra)
        
    return response

app.include_router(router, prefix=path_prefix)