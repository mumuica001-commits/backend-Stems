class StemsAIError(Exception):
    """Base para todas as exceções de domínio."""


class UnsupportedAudioFormatError(StemsAIError):
    def __init__(self, extension: str):
        super().__init__(f"Formato de áudio não suportado: '{extension}'")
        self.extension = extension


class JobNotFoundError(StemsAIError):
    def __init__(self, job_id: str):
        super().__init__(f"Job não encontrado: '{job_id}'")
        self.job_id = job_id


class SeparationEngineError(StemsAIError):
    def __init__(self, engine: str, reason: str):
        super().__init__(f"Falha no engine de separação '{engine}': {reason}")
        self.engine = engine
        self.reason = reason


class AudioTooLargeError(StemsAIError):
    def __init__(self, size_mb: float, limit_mb: float):
        super().__init__(f"Arquivo de {size_mb:.1f}MB excede o limite de {limit_mb:.1f}MB")
