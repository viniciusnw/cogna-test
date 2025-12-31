import logging
import structlog
from pathlib import Path
from datetime import datetime
import sys


def setup_logging(log_dir: str = "/app/logs", log_level: str = "INFO"):
    """
    Configura sistema de logging estruturado com saída para console e arquivo
    """
    # Criar diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo de log com data
    log_file = log_path / f"micro-rag-{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Timestamper compartilhado
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    
    # Processors compartilhados
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Configurar logging padrão do Python
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )
    
    # Configurar structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar formatters
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    
    # Aplicar formatter aos handlers
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
    
    logger = structlog.get_logger()
    logger.info("Logging system initialized", log_file=str(log_file), log_level=log_level)
    
    return logger
