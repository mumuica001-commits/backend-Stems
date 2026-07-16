"""
Funções de tarefa executadas pelo worker RQ.

IMPORTANTE: RQ serializa o job enfileirado como uma string de import
("módulo.função"), não como um objeto Python de fato. Isso significa que
a função enfileirada PRECISA ser importável no nível de módulo — uma
closure definida dentro de um método (`def _run(): ...` dentro de
`enqueue_processing`) não tem um caminho de import válido e falha em
runtime no worker, mesmo que o enqueue em si não dê erro nenhum.
"""
from __future__ import annotations


def process_separation_job(job_id: str) -> None:
    # import local pra evitar import circular entre app.api e workers
    from app.application.use_cases.process_job import ProcessJobUseCase

    ProcessJobUseCase().execute(job_id)
