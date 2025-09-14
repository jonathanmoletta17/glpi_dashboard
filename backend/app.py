import logging
from flask import Flask
from flask_cors import CORS

from api.routes import api_bp
from config.settings import active_config
from config.logging_config import configure_structured_logging
from utils.observability_middleware import setup_observability

# from utils.structured_logger import StructuredLogger

# Inicializa o logger estruturado (agora feito dentro de configure_structured_logging)
# structured_logger = StructuredLogger(logger_name="glpi_service", level=active_config().LOG_LEVEL)

# Configuração inicial do logging
configure_structured_logging(log_level=active_config().LOG_LEVEL, log_file=active_config().LOG_FILE_PATH)

# Obtém o logger 'glpi_service' após a configuração
glpi_service_logger = logging.getLogger("glpi_service")
glpi_service_logger.info(f"Nível de log do glpi_service após configuração: {glpi_service_logger.level}")

# Obtém o logger da MetricsFacade (que usa 'glpi_service')
metrics_facade_logger = logging.getLogger("glpi_service")
metrics_facade_logger.info(f"Nível de log da MetricsFacade (glpi_service) após configuração: {metrics_facade_logger.level}")

app = Flask(__name__)

# Configurações do aplicativo
app.config.from_object(active_config())

# Configura CORS
CORS(app, resources={r"/api/*": {"origins": active_config().CORS_ORIGINS}})

# Configura o middleware de observabilidade
setup_observability(app)

# Registra blueprints
app.register_blueprint(api_bp)
# app.register_blueprint(dashboard_bp, url_prefix='/dashboard') # Removendo esta linha

if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
