"""Configurações centralizadas do projeto com validações robustas"""
import logging
import os
import warnings
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()


class ConfigValidationError(Exception):
    """Exceção para erros de validação de configuração"""

    pass


class Config:
    """Configuração base com validações robustas"""

    def __init__(self):
        """Inicializa e valida as configurações"""
        self._validate_required_configs()
        self._validate_config_values()

    # Flask Security Configuration
    @property
    def SECRET_KEY(self) -> str:
        """Secret key with security validation"""
        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            if not self.DEBUG:
                raise ConfigValidationError("SECRET_KEY environment variable is required in production")
            # Development fallback with warning
            import warnings

            warnings.warn("Using development SECRET_KEY. Set SECRET_KEY environment variable for production.")
            return "dev-secret-key-DO-NOT-USE-IN-PRODUCTION"

        # Validate secret key strength in production
        if not self.DEBUG:
            if len(secret_key) < 32:
                raise ConfigValidationError("SECRET_KEY must be at least 32 characters long in production")
            if secret_key in ["dev-secret-key-change-in-production", "dev-secret-key-DO-NOT-USE-IN-PRODUCTION"]:
                raise ConfigValidationError("Default development SECRET_KEY cannot be used in production")

        return secret_key

    # Debug mode - Secure by default
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    @property
    def PORT(self) -> int:
        """Porta do servidor com validação"""
        try:
            port = int(os.environ.get("PORT", 8000))
            if not (1 <= port <= 65535):
                raise ValueError(f"Porta inválida: {port}")
            return port
        except ValueError as e:
            raise ConfigValidationError(f"Erro na configuração PORT: {e}")

    HOST = os.environ.get("HOST", "127.0.0.1")

    # GLPI API
    GLPI_URL = os.environ.get("GLPI_URL", "http://10.73.0.79/glpi/apirest.php")
    GLPI_USER_TOKEN = os.environ.get("GLPI_USER_TOKEN")
    GLPI_APP_TOKEN = os.environ.get("GLPI_APP_TOKEN")

    # Mock Data Mode - Para desenvolvimento e testes da interface
    USE_MOCK_DATA = os.environ.get("USE_MOCK_DATA", "False").lower() == "true"

    # Backend API
    BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000")
    API_KEY = os.environ.get("API_KEY", "")

    # Observabilidade
    PROMETHEUS_GATEWAY_URL = os.environ.get("PROMETHEUS_GATEWAY_URL", "http://localhost:9091")
    PROMETHEUS_JOB_NAME = os.environ.get("PROMETHEUS_JOB_NAME", "glpi_dashboard")
    STRUCTURED_LOGGING = os.environ.get("STRUCTURED_LOGGING", "True").lower() == "true"

    @property
    def LOG_FILE_PATH(self) -> str:
        """Log file path with directory validation"""
        log_path = os.environ.get("LOG_FILE_PATH", "logs/app.log")

        # Ensure log directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, mode=0o755, exist_ok=True)
            except OSError as e:
                raise ConfigValidationError(f"Cannot create log directory '{log_dir}': {e}")

        return log_path

    LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5"))

    # Alertas
    ALERT_RESPONSE_TIME_THRESHOLD = float(os.environ.get("ALERT_RESPONSE_TIME_THRESHOLD", "300"))  # 300ms
    ALERT_ERROR_RATE_THRESHOLD = float(os.environ.get("ALERT_ERROR_RATE_THRESHOLD", "0.05"))  # 5%
    ALERT_ZERO_TICKETS_THRESHOLD = int(os.environ.get("ALERT_ZERO_TICKETS_THRESHOLD", "60"))  # 60 segundos

    @property
    def API_TIMEOUT(self) -> int:
        """Timeout da API com validação"""
        try:
            timeout = int(os.environ.get("API_TIMEOUT", "30"))
            if not (1 <= timeout <= 300):
                raise ValueError(f"Timeout deve estar entre 1 e 300 segundos: {timeout}")
            return timeout
        except ValueError as e:
            raise ConfigValidationError(f"Erro na configuração API_TIMEOUT: {e}")

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS - Security: Use environment-configurable allowlist
    @property
    def CORS_ORIGINS(self) -> list:
        """CORS origins with security validation"""
        origins = os.environ.get("CORS_ORIGINS", "").strip()
        if not origins:
            # Secure default: no wildcards in production
            if not self.DEBUG:
                raise ConfigValidationError(
                    "CORS_ORIGINS must be explicitly set in production. " "Use comma-separated list of allowed origins."
                )
            # Development default - still restricted
            return ["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:3000", "http://127.0.0.1:5000"]

        # Parse and validate origins
        origin_list = [origin.strip() for origin in origins.split(",") if origin.strip()]

        # Security validation: no wildcards in production
        if not self.DEBUG and "*" in origin_list:
            raise ConfigValidationError("Wildcard CORS origins (*) are not allowed in production for security reasons")

        return origin_list

    # Redis Cache
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL", os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

    @property
    def CACHE_DEFAULT_TIMEOUT(self) -> int:
        """Timeout do cache com validação"""
        try:
            timeout = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300"))
            if not (10 <= timeout <= 3600):
                raise ValueError(f"Cache timeout deve estar entre 10 e 3600 segundos: {timeout}")
            return timeout
        except ValueError as e:
            raise ConfigValidationError(f"Erro na configuração CACHE_DEFAULT_TIMEOUT: {e}")

    CACHE_KEY_PREFIX = os.environ.get("CACHE_KEY_PREFIX", "glpi_dashboard:")

    # Performance Settings
    @property
    def PERFORMANCE_TARGET_P95(self) -> int:
        """Target de performance P95 com validação"""
        try:
            target = int(os.environ.get("PERFORMANCE_TARGET_P95", "300"))
            if not (50 <= target <= 10000):
                raise ValueError(f"Performance target deve estar entre 50 e 10000ms: {target}")
            return target
        except ValueError as e:
            raise ConfigValidationError(f"Erro na configuração PERFORMANCE_TARGET_P95: {e}")

    # Configurações de segurança
    @property
    def MAX_CONTENT_LENGTH(self) -> int:
        """Tamanho máximo de conteúdo"""
        return int(os.environ.get("MAX_CONTENT_LENGTH", "16777216"))  # 16MB

    @property
    def RATE_LIMIT_PER_MINUTE(self) -> int:
        """Limite de requisições por minuto"""
        return int(os.environ.get("RATE_LIMIT_PER_MINUTE", "100"))

    def _validate_required_configs(self) -> None:
        """Valida configurações obrigatórias"""
        # Em desenvolvimento, GLPI pode não estar configurado ainda
        if self.DEBUG:
            # Em modo debug, apenas avisa sobre configurações faltantes
            if not self.GLPI_USER_TOKEN or not self.GLPI_APP_TOKEN:
                import warnings

                warnings.warn("GLPI credentials not configured. Some features may not work properly.")
            return

        required_configs = {
            "GLPI_URL": self.GLPI_URL,
            "GLPI_USER_TOKEN": self.GLPI_USER_TOKEN,
            "GLPI_APP_TOKEN": self.GLPI_APP_TOKEN,
        }

        missing_configs = [key for key, value in required_configs.items() if not value]

        if missing_configs:
            raise ConfigValidationError(f"Configurações obrigatórias ausentes: {', '.join(missing_configs)}")

    def _validate_config_values(self) -> None:
        """Valida valores das configurações"""
        # Validar URL do GLPI (apenas em produção)
        if not self.DEBUG and not self.GLPI_URL.startswith(("http://", "https://")):
            raise ConfigValidationError(f"GLPI_URL deve começar com http:// ou https://: {self.GLPI_URL}")

        # Validar nível de log
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL.upper() not in valid_log_levels:
            warnings.warn(f"LOG_LEVEL inválido '{self.LOG_LEVEL}', usando 'INFO'")
            self.LOG_LEVEL = "INFO"

        # Additional production security validations
        if not self.DEBUG:
            # Validate HTTPS is enforced in production URLs
            if self.BACKEND_API_URL.startswith("http://") and not self.BACKEND_API_URL.startswith("http://localhost"):
                import warnings

                warnings.warn(f"BACKEND_API_URL should use HTTPS in production: {self.BACKEND_API_URL}")

            # Validate Redis security in production
            if self.REDIS_URL.startswith("redis://") and not self.REDIS_URL.startswith("redis://localhost"):
                import warnings

                warnings.warn("Consider using Redis with TLS (rediss://) in production")

            # Ensure production logging is properly configured
            if self.LOG_LEVEL == "DEBUG":
                import warnings

                warnings.warn("DEBUG logging level may expose sensitive information in production")

    @classmethod
    def configure_logging(cls) -> logging.Logger:
        """Configura o sistema de logging de forma robusta"""
        try:
            config_instance = cls()
            numeric_level = getattr(logging, config_instance.LOG_LEVEL.upper(), None)
            if not isinstance(numeric_level, int):
                numeric_level = logging.INFO

            # Configurar logging básico
            logging.basicConfig(
                level=numeric_level,
                format=config_instance.LOG_FORMAT,
                force=True,  # Força reconfiguração
            )

            # Configurar loggers específicos
            logger = logging.getLogger("api")
            logger.setLevel(numeric_level)

            # Reduzir verbosidade de bibliotecas externas
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("requests").setLevel(logging.WARNING)

            return logger

        except Exception as e:
            # Fallback para configuração básica
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logger = logging.getLogger("api")
            logger.warning(f"Erro na configuração de logging: {e}")
            return logger

    def get_config_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das configurações (sem dados sensíveis)"""
        # Usar o redator de dados sensíveis para criar resumo seguro
        try:
            from utils.structured_logging import SensitiveDataRedactor

            return SensitiveDataRedactor.create_safe_config_summary(self)
        except ImportError:
            # Fallback para resumo básico sem dados sensíveis
            return {
                "debug": self.DEBUG,
                "port": self.PORT,
                "host": self.HOST if self.HOST != "0.0.0.0" else "***REDACTED_HOST***",
                "glpi_url": "***REDACTED_GLPI_URL***" if not self.DEBUG else self.GLPI_URL,
                "log_level": self.LOG_LEVEL,
                "cache_type": self.CACHE_TYPE,
                "cache_timeout": self.CACHE_DEFAULT_TIMEOUT,
                "performance_target": self.PERFORMANCE_TARGET_P95,
                "api_timeout": self.API_TIMEOUT,
                "credentials_configured": {
                    "glpi_user_token": bool(self.GLPI_USER_TOKEN),
                    "glpi_app_token": bool(self.GLPI_APP_TOKEN),
                    "secret_key": bool(getattr(self, "SECRET_KEY", None)),
                    "api_key": bool(self.API_KEY),
                },
            }


# Configuração de desenvolvimento
class DevelopmentConfig(Config):
    """Configuração para ambiente de desenvolvimento"""

    DEBUG = True


# Configuração de produção
class ProductionConfig(Config):
    """Configuração para ambiente de produção com segurança aprimorada"""

    DEBUG = False

    # Security: Require explicit CORS configuration in production
    @property
    def CORS_ORIGINS(self) -> list:
        """CORS origins - must be explicitly configured in production"""
        origins = os.environ.get("CORS_ORIGINS", "").strip()
        if not origins:
            raise ConfigValidationError(
                "CORS_ORIGINS environment variable is required in production. "
                "Set to comma-separated list of allowed origins (e.g., 'https://app.example.com,https://dashboard.example.com')"
            )

        origin_list = [origin.strip() for origin in origins.split(",") if origin.strip()]

        # Security validation: no wildcards or insecure protocols in production
        for origin in origin_list:
            if "*" in origin:
                raise ConfigValidationError(f"Wildcard CORS origin not allowed in production: {origin}")
            if origin.startswith("http://") and not origin.startswith("http://localhost"):
                import warnings

                warnings.warn(f"HTTP (non-HTTPS) CORS origin in production is insecure: {origin}")

        return origin_list

    # Production security settings
    @property
    def HOST(self) -> str:
        """Production host binding - default to all interfaces"""
        return os.environ.get("HOST", "0.0.0.0")

    # Security headers configuration
    SECURITY_HEADERS = {
        "STRICT_TRANSPORT_SECURITY": "max-age=31536000; includeSubDomains; preload",
        "X_CONTENT_TYPE_OPTIONS": "nosniff",
        "X_FRAME_OPTIONS": "DENY",
        "X_XSS_PROTECTION": "1; mode=block",
        "REFERRER_POLICY": "strict-origin-when-cross-origin",
        "CONTENT_SECURITY_POLICY": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
    }


# Configuração de teste
class TestingConfig(Config):
    """Configuração para ambiente de teste"""

    DEBUG = True
    TESTING = True


# Dicionário de configurações
config_by_name = {
    "dev": DevelopmentConfig,
    "development": DevelopmentConfig,
    "prod": ProductionConfig,
    "production": ProductionConfig,
    "test": TestingConfig,
}

# Configuração ativa
active_config = config_by_name[os.environ.get("FLASK_ENV", "dev")]


def get_config():
    """Retorna a configuração ativa baseada na variável de ambiente FLASK_ENV"""
    return active_config()
