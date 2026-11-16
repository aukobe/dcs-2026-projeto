$ .venv/bin/python -m pytest tests/unidade/test_readme.py -v
tests/unidade/test_readme.py::test_secoes_obrigatorias_na_ordem PASSED   [  5%]
tests/unidade/test_readme.py::test_servico_listado[GitHub Actions] PASSED [ 11%]
tests/unidade/test_readme.py::test_servico_listado[Codespaces] PASSED    [ 17%]
tests/unidade/test_readme.py::test_servico_listado[TCGCSV] PASSED        [ 23%]
tests/unidade/test_readme.py::test_servico_listado[Banco Central] PASSED [ 29%]
tests/unidade/test_readme.py::test_servico_listado[RustFS] PASSED        [ 35%]
tests/unidade/test_readme.py::test_servico_listado[MinIO] PASSED         [ 41%]
tests/unidade/test_readme.py::test_servico_listado[Python 3.13] PASSED   [ 47%]
tests/unidade/test_readme.py::test_todo_servico_da_tabela_e_gratuito PASSED [ 52%]
tests/unidade/test_readme.py::test_como_rodar_do_clone_limpo_na_ordem PASSED [ 58%]
tests/unidade/test_readme.py::test_diferenca_entre_minio_local_e_data_lake_da_turma PASSED [ 64%]
tests/unidade/test_readme.py::test_horarios_da_coleta_iguais_aos_do_workflow PASSED [ 70%]
tests/unidade/test_readme.py::test_riscos_r01_pela_regra_do_adr_007_e_r02 PASSED [ 76%]
tests/unidade/test_readme.py::test_tabela_dias_sem_coleta_no_formato_do_verificador PASSED [ 82%]
tests/unidade/test_readme.py::test_observacao_de_04_11_fica_fora_da_tabela PASSED [ 88%]
tests/unidade/test_readme.py::test_links_relativos_apontam_para_arquivos_existentes PASSED [ 94%]
tests/unidade/test_readme.py::test_nenhuma_credencial_no_readme PASSED   [100%]
============================== 17 passed in 0.09s ==============================

$ .venv/bin/python -m pytest tests/unidade -q
419 passed in 45.79s

# Ajuste do README (P2, cesta_raras sem Code Card, R-02), 2026-11-16
$ .venv/bin/python -m pytest tests/unidade/test_readme.py -v
tests/unidade/test_readme.py::test_secoes_obrigatorias_na_ordem PASSED   [  5%]
tests/unidade/test_readme.py::test_servico_listado[GitHub Actions] PASSED [ 11%]
tests/unidade/test_readme.py::test_servico_listado[Codespaces] PASSED    [ 17%]
tests/unidade/test_readme.py::test_servico_listado[TCGCSV] PASSED        [ 23%]
tests/unidade/test_readme.py::test_servico_listado[Banco Central] PASSED [ 29%]
tests/unidade/test_readme.py::test_servico_listado[RustFS] PASSED        [ 35%]
tests/unidade/test_readme.py::test_servico_listado[MinIO] PASSED         [ 41%]
tests/unidade/test_readme.py::test_servico_listado[Python 3.13] PASSED   [ 47%]
tests/unidade/test_readme.py::test_todo_servico_da_tabela_e_gratuito PASSED [ 52%]
tests/unidade/test_readme.py::test_como_rodar_do_clone_limpo_na_ordem PASSED [ 58%]
tests/unidade/test_readme.py::test_diferenca_entre_minio_local_e_data_lake_da_turma PASSED [ 64%]
tests/unidade/test_readme.py::test_horarios_da_coleta_iguais_aos_do_workflow PASSED [ 70%]
tests/unidade/test_readme.py::test_riscos_r01_pela_regra_do_adr_007_e_r02 PASSED [ 76%]
tests/unidade/test_readme.py::test_tabela_dias_sem_coleta_no_formato_do_verificador PASSED [ 82%]
tests/unidade/test_readme.py::test_observacao_de_04_11_fica_fora_da_tabela PASSED [ 88%]
tests/unidade/test_readme.py::test_links_relativos_apontam_para_arquivos_existentes PASSED [ 94%]
tests/unidade/test_readme.py::test_nenhuma_credencial_no_readme PASSED   [100%]
============================== 17 passed in 0.09s ==============================

# Correção do R-02 (afirmação não confirmada retirada), 2026-11-16
$ .venv/bin/python -m pytest tests/unidade/test_readme.py -v
tests/unidade/test_readme.py::test_secoes_obrigatorias_na_ordem PASSED   [  5%]
tests/unidade/test_readme.py::test_servico_listado[GitHub Actions] PASSED [ 11%]
tests/unidade/test_readme.py::test_servico_listado[Codespaces] PASSED    [ 17%]
tests/unidade/test_readme.py::test_servico_listado[TCGCSV] PASSED        [ 23%]
tests/unidade/test_readme.py::test_servico_listado[Banco Central] PASSED [ 29%]
tests/unidade/test_readme.py::test_servico_listado[RustFS] PASSED        [ 35%]
tests/unidade/test_readme.py::test_servico_listado[MinIO] PASSED         [ 41%]
tests/unidade/test_readme.py::test_servico_listado[Python 3.13] PASSED   [ 47%]
tests/unidade/test_readme.py::test_todo_servico_da_tabela_e_gratuito PASSED [ 52%]
tests/unidade/test_readme.py::test_como_rodar_do_clone_limpo_na_ordem PASSED [ 58%]
tests/unidade/test_readme.py::test_diferenca_entre_minio_local_e_data_lake_da_turma PASSED [ 64%]
tests/unidade/test_readme.py::test_horarios_da_coleta_iguais_aos_do_workflow PASSED [ 70%]
tests/unidade/test_readme.py::test_riscos_r01_pela_regra_do_adr_007_e_r02 PASSED [ 76%]
tests/unidade/test_readme.py::test_tabela_dias_sem_coleta_no_formato_do_verificador PASSED [ 82%]
tests/unidade/test_readme.py::test_observacao_de_04_11_fica_fora_da_tabela PASSED [ 88%]
tests/unidade/test_readme.py::test_links_relativos_apontam_para_arquivos_existentes PASSED [ 94%]
tests/unidade/test_readme.py::test_nenhuma_credencial_no_readme PASSED   [100%]
============================== 17 passed in 0.09s ==============================
