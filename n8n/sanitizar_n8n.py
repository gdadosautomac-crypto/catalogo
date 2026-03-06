"""
sanitizar_n8n.py
================
Sanitiza tokens e credenciais em JSONs exportados do N8N antes do commit no GitHub.

USO:
    python sanitizar_n8n.py --pasta "C:/repo/catalogo/n8n"

RESULTADO:
    - Cria uma pasta "sanitizados/" dentro da pasta informada
    - Copia todos os JSONs sanitizados para la (originais intactos)
    - Gera um relatorio "relatorio_sanitizacao.txt" com tudo que foi substituido
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# CAMPOS SENSIVEIS NO JSON DO N8N
# ─────────────────────────────────────────────

CAMPOS_SENSIVEIS = [
    "apiKey", "api_key", "apikey",
    "accessToken", "access_token",
    "refreshToken", "refresh_token",
    "clientSecret", "client_secret",
    "clientId", "client_id",
    "password", "passwd", "secret",
    "token", "bearerToken", "bearer_token",
    "webhookId", "webhook_id",
    "authToken", "auth_token",
    "privateKey", "private_key",
    "serviceAccountKey",
    "instanceId", "instance_id",
    "phoneToken", "phone_token",
    "instanceToken",
    "zapiToken", "zapi_token",
    "supabaseKey", "supabase_key", "supabaseUrl",
    "anonKey", "anon_key",
    "databaseUrl", "database_url",
    "connectionString", "connection_string",
    "dsn",
    "smtp_password", "smtpPassword",
    "encryptionKey", "encryption_key",
    "notionToken", "notion_token",
    "slackToken", "slack_token",
    "openaiApiKey", "openai_api_key",
]

CAMPOS_IGNORAR = [
    "id", "name", "type", "node", "nodeType", "position",
    "typeVersion", "notesInFlow", "pinData", "versionId",
    "meta", "tags", "active", "settings", "staticData",
    "createdAt", "updatedAt", "color", "notes",
]

PADROES_VALOR_TOKEN = [
    (r'eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', 'JWT_TOKEN'),
    (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY'),
    (r'(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@\S+', 'DB_CONNECTION_WITH_CREDENTIALS'),
]


def gerar_placeholder(campo):
    resultado = re.sub(r'(?<!^)(?=[A-Z])', '_', campo).upper()
    resultado = re.sub(r'[^A-Z0-9_]', '_', resultado)
    return "{{" + resultado + "}}"


def sanitizar_valor(campo, valor):
    if campo.lower() in [c.lower() for c in CAMPOS_IGNORAR]:
        return valor, False, None

    if not isinstance(valor, str) or len(valor) < 8:
        return valor, False, None

    for campo_sensivel in CAMPOS_SENSIVEIS:
        if campo.lower() == campo_sensivel.lower():
            placeholder = gerar_placeholder(campo)
            return placeholder, True, "campo sensivel '{}'".format(campo)

    for padrao, nome_tipo in PADROES_VALOR_TOKEN:
        if re.search(padrao, valor, re.IGNORECASE):
            placeholder = "{{" + nome_tipo + "}}"
            return placeholder, True, "padrao de token detectado ({})".format(nome_tipo)

    return valor, False, None


def sanitizar_objeto(obj, caminho="", substituicoes=None):
    if substituicoes is None:
        substituicoes = []

    if isinstance(obj, dict):
        novo = {}
        for chave, valor in obj.items():
            caminho_atual = "{}.{}".format(caminho, chave) if caminho else chave
            if isinstance(valor, (dict, list)):
                novo[chave] = sanitizar_objeto(valor, caminho_atual, substituicoes)
            else:
                valor_novo, substituido, motivo = sanitizar_valor(chave, valor)
                novo[chave] = valor_novo
                if substituido:
                    substituicoes.append({
                        "caminho": caminho_atual,
                        "motivo": motivo,
                        "placeholder": valor_novo
                    })
        return novo

    elif isinstance(obj, list):
        return [sanitizar_objeto(item, "{}[{}]".format(caminho, i), substituicoes)
                for i, item in enumerate(obj)]

    return obj


def processar_pasta(pasta_origem):
    pasta = Path(pasta_origem)

    if not pasta.exists():
        print("ERRO: Pasta nao encontrada: {}".format(pasta_origem))
        return

    jsons = list(pasta.glob("*.json"))
    if not jsons:
        print("AVISO: Nenhum arquivo .json encontrado em: {}".format(pasta_origem))
        return

    pasta_saida = pasta / "sanitizados"
    pasta_saida.mkdir(exist_ok=True)

    print("")
    print("Encontrados {} arquivos JSON".format(len(jsons)))
    print("Salvando sanitizados em: {}".format(pasta_saida))
    print("")

    relatorio_linhas = [
        "RELATORIO DE SANITIZACAO - {}".format(datetime.now().strftime('%d/%m/%Y %H:%M')),
        "Pasta: {}".format(pasta_origem),
        "Total de arquivos: {}".format(len(jsons)),
        "=" * 60,
        ""
    ]

    total_substituicoes = 0
    arquivos_limpos = 0
    arquivos_com_substituicoes = 0

    for arquivo in sorted(jsons):
        try:
            conteudo = arquivo.read_text(encoding="utf-8")
            obj = json.loads(conteudo)
        except Exception as e:
            print("  ERRO ao ler {}: {}".format(arquivo.name, e))
            relatorio_linhas.append("ERRO - {}: {}\n".format(arquivo.name, e))
            continue

        substituicoes = []
        obj_sanitizado = sanitizar_objeto(obj, substituicoes=substituicoes)

        arquivo_saida = pasta_saida / arquivo.name
        arquivo_saida.write_text(
            json.dumps(obj_sanitizado, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        if substituicoes:
            arquivos_com_substituicoes += 1
            total_substituicoes += len(substituicoes)
            print("  [SANITIZADO] {} - {} substituicao(oes)".format(arquivo.name, len(substituicoes)))
            relatorio_linhas.append("{} ({} substituicao(oes)):".format(arquivo.name, len(substituicoes)))
            for s in substituicoes:
                relatorio_linhas.append("   * {} -> {}  [{}]".format(s['caminho'], s['placeholder'], s['motivo']))
            relatorio_linhas.append("")
        else:
            arquivos_limpos += 1
            print("  [OK] {} - nenhum token detectado".format(arquivo.name))

    relatorio_linhas.append("")
    relatorio_linhas.append("=" * 60)
    relatorio_linhas.append("RESUMO")
    relatorio_linhas.append("  Arquivos processados:          {}".format(len(jsons)))
    relatorio_linhas.append("  Arquivos sem tokens:           {}".format(arquivos_limpos))
    relatorio_linhas.append("  Arquivos com substituicoes:    {}".format(arquivos_com_substituicoes))
    relatorio_linhas.append("  Total de substituicoes feitas: {}".format(total_substituicoes))
    relatorio_linhas.append("")
    relatorio_linhas.append("Arquivos sanitizados prontos para commit em:")
    relatorio_linhas.append("  {}".format(pasta_saida))

    relatorio_path = pasta_saida / "relatorio_sanitizacao.txt"
    relatorio_path.write_text("\n".join(relatorio_linhas), encoding="utf-8")

    print("")
    print("=" * 50)
    print("Concluido!")
    print("  Arquivos processados:       {}".format(len(jsons)))
    print("  Com substituicoes:          {}".format(arquivos_com_substituicoes))
    print("  Total de tokens removidos:  {}".format(total_substituicoes))
    print("  Relatorio salvo em:         {}".format(relatorio_path))
    print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sanitiza tokens em JSONs exportados do N8N antes do commit no GitHub."
    )
    parser.add_argument(
        "--pasta",
        required=True,
        help="Caminho para a pasta com os JSONs."
    )
    args = parser.parse_args()
    processar_pasta(args.pasta)