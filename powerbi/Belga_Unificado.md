# 📊 Belga Unificado — Documentação Técnica

> **Notion:** _[adicionar link da entrada no catálogo]_
> **Power BI Service:** _[adicionar link do workspace após publicação]_
> **Última atualização:** 2026-03-23
> **Responsável:** André

---

## 1. Objetivo

Dashboard analítico unificado da **Belga Polímeros**, consolidando visões de consumo de matéria-prima, expedição, estoque, produção e pedidos a expedir. Suporta decisões operacionais e gerenciais da área Industrial/Comercial da unidade Belga.

- **Quem usa:** Gestão Industrial / Comercial / Diretoria Belga
- **Frequência de consulta:** Operacional (diário/semanal)
- **Áreas cobertas:** Consumo de MP, composição de KITs, estoque, expedição, pedidos a expedir, pré-romaneio

---

## 2. Fontes de Dados

Todas as tabelas Import conectam diretamente ao **PostgreSQL** via `Value.NativeQuery`. **Não há arquivos Excel** — diferente do TONELADA_VENDA_PRODUZIDA.

| Tabela | Tipo | Origem SQL | Banco |
|---|---|---|---|
| `A Expedir` | Import / M | Query customizada | `marcolan_carga` @ 10.201.100.201 |
| `Expedido` | Import / M | `entregas_geral` | `marcolan_carga` |
| `1 - Consumo SQL` | Import / M | `belga_consumo` | `marcolan_carga` |
| `1 - Produtos Custo MP` | Import / M | `belga_produtos_custo_mp` | `marcolan_carga` |
| `2 - Produtos PK` | Import / M | `belga_produtos_pk` | `marcolan_carga` |
| `2 - Composição_KIT PK` | Import / M | `belga_composicao_kit_pk` | `marcolan_carga` |
| `PRE_ROMANEIO` | Import / M | `belga_pre_romaneio` | `marcolan_carga` |
| `Composicao` | Import / M | `belga_composicao` | `marcolan_carga` |
| `4 - fato_posicao_atual` | Import / M | Query customizada (CTE) | `marcolan_carga` |
| `4-fato_evolucao_saldo` | Import / M | Query customizada | `marcolan_carga` |
| `4 - fato_entrada_saida` | Import / M | Query customizada | `marcolan_carga` |
| `estoque_raw` | Import / M | `estoque_produtos` | `marcolan_carga` |
| `1 - MP Consumo Custo` | Calculated (DAX) | — | — |
| `1 - MP Mapeadas` | Calculated (DAX) | — | — |
| `1 - Produtos Custo Único` | Calculated (DAX) | — | — |
| `2 - Calendario_Evolucao` | Calculated (DAX) | — | — |
| `Calendario` | Calculated (DAX) | — | — |
| `Produtos PK - Cadastro` | Calculated (DAX) | — | — |

> **Servidor:** `10.201.100.201` — IP interno (rede local). Não funciona fora da VPN/rede.

---

## 3. Queries SQL (Power Query M) — Completas

### 3.1 A Expedir
> Pedidos abertos/em separação da Belga Polímeros, com cruzamento de estoque disponível para calcular situação e saldo.

```sql
SELECT
    p.tipo_unidade,
    p.unidade,
    p.data_hora_pedido,
    p.cod_pedido,
    p.status_pedido,
    TO_CHAR(
        ROUND(p.valor_unitario_total_com_desconto::numeric, 2),
        'FM9999999990D99'
    ) AS valor_unitario_total_com_desconto_formatado,
    p.cod_cliente,
    p.nome_cliente,
    p.cod_produto,
    p.nome_produto,
    p.categoria_produto,
    p.classe_produto,
    p.sub_classe_produto,
    p.qtd_produto,
    ep.estoque_qtd,
    (
        ep.estoque_qtd
        - REPLACE(p.qtd_produto, ',', '.')::numeric
    ) AS saldo_estoque,
    CASE
        WHEN ep.estoque_qtd >= REPLACE(p.qtd_produto, ',', '.')::numeric
        THEN 'Disponível'
        ELSE 'Insuficiente'
    END AS situacao_estoque
FROM pedidos p
LEFT JOIN estoque_completo_produtos ep
       ON ep.nome_produto = p.nome_produto
      AND ep.unidade      = p.unidade
WHERE p.unidade = 'BELGA POLIMEROS'
  AND p.status_pedido IN ('Aberto', 'Em Separacao')
```

### 3.2 Expedido
> Entregas realizadas pela Belga a partir de 2025-07-01.

```sql
SELECT * FROM entregas_geral eg
WHERE eg.data_hora_entregue >= '2025-07-01'
  AND unidade = 'BELGA POLIMEROS'
```

> ⚠️ **Data hardcoded:** `>= '2025-07-01'` — atualizar manualmente conforme necessário.

### 3.3 1 - Consumo SQL
> Lê diretamente da tabela `belga_consumo`, que é alimentada pelo ETL N8N (workflow `ETL Belga MySQL → PostgreSQL`).

```sql
SELECT * FROM belga_consumo bc
```

### 3.4 1 - Produtos Custo MP

```sql
SELECT * FROM belga_produtos_custo_mp bpcm
```

### 3.5 2 - Produtos PK

```sql
SELECT * FROM belga_produtos_pk bpp
```

### 3.6 2 - Composição_KIT PK

```sql
SELECT * FROM belga_composicao_kit_pk bckp
```

### 3.7 PRE_ROMANEIO

```sql
SELECT * FROM belga_pre_romaneio bpr
```

### 3.8 Composicao

```sql
SELECT * FROM belga_composicao bc
```

### 3.9 4 - fato_posicao_atual
> CTE complexa: calcula posição atual de estoque + média mensal de vendas (jan-fev/2026) + cobertura em meses + status crítico/atenção/OK.

```sql
WITH
posicao_atual AS (
    SELECT
        cod_produto,
        nome_produto,
        categoria,
        classe,
        subclasse,
        CAST(REPLACE(estoque_atual, ',', '.') AS numeric) AS estoque_atual,
        CAST(REPLACE(custo_unitario, ',', '.') AS numeric) AS custo_unitario,
        CAST(REPLACE(estoque_atual, ',', '.') AS numeric)
            * CAST(REPLACE(custo_unitario, ',', '.') AS numeric) AS valor_estoque
    FROM (
        SELECT DISTINCT ON (cod_produto)
            cod_produto, nome_produto, categoria, classe, subclasse,
            estoque_atual, custo_unitario, data_movimentacao
        FROM estoque_produtos
        WHERE unidade = 'BELGA POLIMEROS'
        ORDER BY cod_produto, data_movimentacao DESC
    ) sub
),
media_vendas AS (
    SELECT
        cod_produto,
        SUM(ABS(CAST(REPLACE(qtd_movimentacao, ',', '.') AS numeric))) / 2.0 AS media_mensal_vendas
    FROM estoque_produtos
    WHERE unidade = 'BELGA POLIMEROS'
        AND tipo_movimentacao = 'VENDA'
        AND data_movimentacao::date BETWEEN '2026-01-01' AND '2026-02-28'  -- ⚠️ hardcoded
    GROUP BY cod_produto
)
SELECT
    pa.cod_produto,
    pa.nome_produto,
    pa.categoria,
    pa.classe,
    pa.subclasse,
    pa.estoque_atual,
    pa.custo_unitario,
    pa.valor_estoque,
    mv.media_mensal_vendas,
    CASE
        WHEN mv.media_mensal_vendas > 0
        THEN ROUND((pa.estoque_atual / mv.media_mensal_vendas), 1)
        ELSE NULL
    END AS cobertura_meses,
    ROUND(mv.media_mensal_vendas, 0) AS estoque_minimo_sugerido,
    CASE
        WHEN pa.estoque_atual <= mv.media_mensal_vendas        THEN 'CRÍTICO'
        WHEN pa.estoque_atual <= mv.media_mensal_vendas * 2   THEN 'ATENÇÃO'
        ELSE 'OK'
    END AS status_estoque
FROM posicao_atual pa
LEFT JOIN media_vendas mv ON pa.cod_produto = mv.cod_produto
ORDER BY cobertura_meses ASC NULLS LAST
```

> ⚠️ **Datas hardcoded:** `BETWEEN '2026-01-01' AND '2026-02-28'` para cálculo da média de vendas. Atualizar mensalmente.

### 3.10 4-fato_evolucao_saldo
> Saldo diário de estoque por produto, a partir de 2026-01-01.

```sql
SELECT
    cod_produto,
    nome_produto,
    categoria,
    classe,
    subclasse,
    data_movimentacao::date AS data,
    CAST(REPLACE(saldo_dia, ',', '.') AS numeric) AS estoque_fechamento
FROM (
    SELECT DISTINCT ON (cod_produto, data_movimentacao::date)
        cod_produto, nome_produto, categoria, classe, subclasse,
        data_movimentacao, saldo_dia
    FROM estoque_produtos
    WHERE unidade = 'BELGA POLIMEROS'
        AND data_movimentacao::date >= '2026-01-01'  -- ⚠️ hardcoded
    ORDER BY cod_produto, data_movimentacao::date, data_movimentacao DESC
) sub
ORDER BY cod_produto, data
```

### 3.11 4 - fato_entrada_saida
> Entradas e saídas mensais agregadas por produto e tipo de movimentação, a partir de 2026-01-01.

```sql
SELECT
    cod_produto,
    nome_produto,
    categoria,
    classe,
    subclasse,
    DATE_TRUNC('month', data_movimentacao::timestamp)::date AS mes,
    tipo_movimentacao,
    observacao,
    SUM(ABS(CAST(REPLACE(qtd_movimentacao, ',', '.') AS numeric))) AS qtd_total,
    SUM(
        ABS(CAST(REPLACE(qtd_movimentacao, ',', '.') AS numeric)) *
        CAST(REPLACE(custo_unitario, ',', '.') AS numeric)
    ) AS valor_total
FROM estoque_produtos
WHERE unidade = 'BELGA POLIMEROS'
    AND data_movimentacao::date >= '2026-01-01'  -- ⚠️ hardcoded
GROUP BY cod_produto, nome_produto, categoria, classe, subclasse, mes, tipo_movimentacao, observacao
ORDER BY mes, cod_produto
```

### 3.12 estoque_raw
> Movimentações brutas de estoque, a partir de 2026-01-01. Granularidade: uma linha por movimentação.

```sql
SELECT
    tipo_unidade,
    unidade,
    id_produto,
    tipo_movimentacao,
    observacao,
    CAST(REPLACE(qtd_movimentacao, ',', '.') AS numeric) AS qtd_movimentacao,
    data_movimentacao::date AS data_movimentacao,
    CAST(REPLACE(saldo_dia, ',', '.') AS numeric) AS saldo_dia,
    cod_movimentacao,
    cod_produto,
    nome_produto,
    categoria,
    classe,
    subclasse,
    CAST(REPLACE(estoque_atual, ',', '.') AS numeric) AS estoque_atual,
    CAST(REPLACE(custo_unitario, ',', '.') AS numeric) AS custo_unitario
FROM estoque_produtos
WHERE unidade = 'BELGA POLIMEROS'
    AND data_movimentacao::date >= '2026-01-01'  -- ⚠️ hardcoded
ORDER BY data_movimentacao, cod_produto
```

---

## 4. Modelo de Dados

### Relacionamentos relevantes (excluindo LocalDateTables automáticas)

| De (Tabela) | De (Coluna) | Para (Tabela) | Para (Coluna) | Cardinalidade | Filtro | Ativo |
|---|---|---|---|---|---|---|
| `1 - Consumo SQL` | desc_mp | `1 - MP Consumo Custo` | desc_mp | N:1 | OneDirection | ✅ |
| `1 - MP Mapeadas` | desc_mp | `1 - Consumo SQL` | desc_mp | **N:N** ⚠️ | BothDirections | ✅ |
| `1 - Produtos Custo MP` | desc_mp | `1 - Consumo SQL` | desc_mp | **N:N** ⚠️ | BothDirections | ✅ |
| `2 - Produtos PK` | codproduto | `2 - Composição_KIT PK` | kit_cod | **N:N** ⚠️ | BothDirections | ✅ |
| `2 - Produtos PK` | codproduto | `Composicao` | cod_produto | N:1 | OneDirection | ✅ |
| `2 - Produtos PK` | codproduto | `4 - fato_posicao_atual` | cod_produto | N:1 | OneDirection | ✅ |
| `4 - fato_entrada_saida` | cod_produto | `4 - fato_posicao_atual` | cod_produto | N:1 | OneDirection | ✅ |
| `4-fato_evolucao_saldo` | cod_produto | `4 - fato_posicao_atual` | cod_produto | N:1 | OneDirection | ✅ |
| `A Expedir` | cod_pedido | `Expedido` | cod_pedido | **N:N** ⚠️ | BothDirections | ✅ |
| `A Expedir` | nome_produto | `Composicao` | desc_produto | **N:N** ⚠️ | BothDirections | ✅ |
| `estoque_raw` | cod_produto | `4 - fato_posicao_atual` | cod_produto | N:1 | OneDirection | ✅ |
| `Expedido` | cod_produto | `Produtos PK - Cadastro` | IdProdutoTexto | N:1 | OneDirection | ✅ |
| `PRE_ROMANEIO` | cod_pedido | `A Expedir` | cod_pedido | **N:N** ⚠️ | BothDirections | ✅ |

> ⚠️ **6 relacionamentos N:N** — testar visuais com filtros cruzados para verificar dupla contagem.

### Diagrama simplificado

```
                    1 - MP Consumo Custo
                           ↑ N:1
1 - MP Mapeadas ←── N:N ── 1 - Consumo SQL ──── N:N ──→ 1 - Produtos Custo MP

2 - Composição_KIT PK ←── N:N ── 2 - Produtos PK ──→ Composicao (N:1)
                                        ↓ N:1
                               4 - fato_posicao_atual ←── 4 - fato_entrada_saida (N:1)
                                        ↑ N:1             ← 4-fato_evolucao_saldo (N:1)
                                   estoque_raw (N:1)

PRE_ROMANEIO ←── N:N ── A Expedir ──── N:N ──→ Expedido ──→ Produtos PK - Cadastro (N:1)
                              ↓ N:N
                          Composicao
```

---

## 5. Medidas DAX — Completas (15 medidas)

### 5.1 Tabela: A Expedir (1 medida)

#### Qtde Necessária para Produzir
> Calcula quanto falta produzir para atender o pedido, considerando estoque disponível. Retorna 0 se o estoque for suficiente.
```dax
Qtde Necessária para Produzir =
VAR QtdPedido  = SUM('A Expedir'[qtd_produto])
VAR QtdEstoque = MAX('A Expedir'[estoque_qtd])
RETURN
    MAX(
        QtdPedido - QtdEstoque,
        0
    )
```

---

### 5.2 Tabela: Expedido (3 medidas)

#### Margem de Lucro
```dax
Margem de Lucro =
SUM('Expedido'[valor_entregue])
- SUM('Expedido'[custo_entregue])
```

#### Margem de Lucro %
```dax
Margem de Lucro % =
DIVIDE(
    [Margem de Lucro],
    SUM('Expedido'[valor_entregue])
)
```

#### Ferragens Expedidas em Kits
> Para cada linha de EXPEDIDO com categoria "KIT FERRAGEM", busca na tabela de composição quantas ferragens compõem o kit e multiplica pela quantidade entregue.
```dax
Ferragens Expedidas em Kits =
SUMX(
    FILTER(
        'Expedido',
        'Expedido'[categoria_produto] = "KIT FERRAGEM"
    ),
    VAR _cod_kit = 'Expedido'[cod_kit_texto]
    VAR _ferragens_por_kit =
        SUMX(
            FILTER(
                ALL('2 - Composição_KIT PK'),
                '2 - Composição_KIT PK'[kit_cod] = _cod_kit
            ),
            '2 - Composição_KIT PK'[qtde_ferragem_por_kit]
        )
    RETURN
        IF(ISBLANK(_ferragens_por_kit), 0, 'Expedido'[qtd_entregue] * _ferragens_por_kit)
)
```

---

### 5.3 Tabela: 1 - Consumo SQL (4 medidas)

#### Custo Total MP
> Custo de todas as matérias-primas consumidas, cruzando quantidade consumida com custo unitário via RELATED.
```dax
Custo Total MP =
SUMX (
    '1 - Consumo SQL',
    '1 - Consumo SQL'[qt_consumo_total] *
    RELATED ( '1 - MP Consumo Custo'[custo_unitario_mp] )
)
```

#### Custo Total (Item Vendido Único)
> Custo por pedido+produto dedupado, evitando dupla contagem quando há múltiplas MPs por produto.
```dax
Custo Total (Item Vendido Único) =
SUMX(
    SUMMARIZE(
        '1 - Consumo SQL',
        '1 - Consumo SQL'[cod_pedido],
        '1 - Consumo SQL'[produto_vendido],
        "CustoItem", MAX('1 - Consumo SQL'[custo_unit]) * MAX('1 - Consumo SQL'[qtde_produto])
    ),
    [CustoItem]
)
```

#### Qtde MP por Produto
> Conta combinações únicas de produto+MP. Para KITs usa o código do KIT; para demais usa a ferragem.
```dax
Qtde MP por Produto =
COUNTROWS(
    DISTINCT(
        SELECTCOLUMNS(
            '1 - Consumo SQL',
            "Produto",
                IF(
                    LEFT('1 - Consumo SQL'[produto_vendido], 3) = "KIT",
                    '1 - Consumo SQL'[produto_vendido],
                    '1 - Consumo SQL'[ferragem]
                ),
            "MP", '1 - Consumo SQL'[componente_final]
        )
    )
)
```

#### Valor Total Pedido Único
> Valor total dedupado por pedido (evita contar múltiplas vezes o mesmo pedido).
```dax
Valor Total Pedido Único =
SUMX(
    DISTINCT('1 - Consumo SQL'[cod_pedido]),
    CALCULATE(
        MAX('1 - Consumo SQL'[vlr_tot_pve])
    )
)
```

---

### 5.4 Tabela: 2 - Produtos PK (6 medidas)

#### Ferragem Consumida
> Multiplica movimentação de KITs pela quantidade de ferragens por kit via GENERATE+RELATEDTABLE.
```dax
Ferragem Consumida =
SUMX(
    GENERATE(
        '2 - Produtos PK',
        RELATEDTABLE('2 - Composição_KIT PK')
    ),
    '2 - Produtos PK'[QtdMovimentacao] * '2 - Composição_KIT PK'[qtde_ferragem_por_kit]
)
```

#### Qtd Produzida Últimos 15 Dias
> Ignora o slicer de calendário (`REMOVEFILTERS`) para sempre mostrar os últimos 15 dias corridos.
```dax
Qtd Produzida Últimos 15 Dias =
VAR Ultimos15 =
    DATESINPERIOD(
        '2 - Calendario_Evolucao'[Date],
        TODAY(),
        -15,
        DAY
    )
RETURN
CALCULATE(
    SUM('2 - Produtos PK'[QtdMovimentacao]),
    Ultimos15,
    REMOVEFILTERS('2 - Calendario_Evolucao')  -- ignora slicer oficial
)
```

#### Qtd Produzida Últimos 7 Dias
> Janela de 7 dias encerrada ontem (TODAY()-1). Usa ALLSELECTED para ignorar filtro de ontem do slicer.
```dax
Qtd Produzida Últimos 7 Dias =
CALCULATE(
    SUM('2 - Produtos PK'[QtdMovimentacao]),
    DATESINPERIOD(
        '2 - Calendario_Evolucao'[Date],
        TODAY() - 1,
        -7,
        DAY
    ),
    ALLSELECTED('2 - Calendario_Evolucao')  -- ignora filtro de ontem
)
```

#### Valor Produzido (Custo Original)
> Valor pelo custo original cadastrado no produto.
```dax
Valor Produzido (Custo Original) =
SUMX(
    '2 - Produtos PK',
    '2 - Produtos PK'[QtdMovimentacao]
        * '2 - Produtos PK'[CustoUnitario]
)
```

#### Valor Produzido 2
> Valor pelo custo ajustado.
```dax
Valor Produzido 2 =
SUMX(
    '2 - Produtos PK',
    '2 - Produtos PK'[QtdMovimentacao]
        * '2 - Produtos PK'[Custo Ajustado]
)
```

#### Valor Produzido Real
> Valor usando MAX do custo por produto para evitar distorção quando há múltiplos registros.
```dax
Valor Produzido Real =
SUMX(
    VALUES('2 - Produtos PK'[NomeProduto]),
    VAR Qtde  = SUM('2 - Produtos PK'[QtdMovimentacao])
    VAR Custo = MAX('2 - Produtos PK'[CustoUnitario])
    RETURN Qtde * Custo
)
```

---

### 5.5 Tabela: Composicao (1 medida)

#### Nylon Total Necessário
> Para cada produto a expedir, busca o consumo de nylon por unidade via LOOKUPVALUE e multiplica pela quantidade do pedido.
```dax
Nylon Total Necessário =
SUMX(
    'A expedir',
    'A expedir'[qtd_produto] *
    LOOKUPVALUE(
        'Composicao'[nylon_por_unidade],
        'Composicao'[desc_produto], 'A expedir'[nome_produto],
        0
    )
)
```

---

## 6. Atualização e Refresh

| Campo | Valor |
|---|---|
| Tipo | Import (DirectQuery via `Value.NativeQuery`) |
| Servidor | `10.201.100.201` (PostgreSQL interno) |
| Banco | `marcolan_carga` |
| Modo atual | Manual — abrir .pbix e clicar em Atualizar |
| Gateway | Necessário para publicar no Service (gateway local apontando para 10.201.100.201) |
| Dataset no Service | _[preencher após publicação]_ |

> ⚠️ O IP `10.201.100.201` é rede interna — para refresh automático no Power BI Service será necessário gateway de dados local na mesma rede.

---

## 7. Dependência com ETL N8N

As tabelas com prefixo `belga_` no banco `marcolan_carga` são alimentadas pelo workflow N8N **"ETL Belga MySQL → PostgreSQL"** (catalogado no Notion). A cadeia de dependência é:

```
ERP Belga (MySQL) → ETL N8N (diário 23h00) → PostgreSQL marcolan_carga → Power BI Belga Unificado
```

Se o ETL falhar, os dados do dashboard ficam desatualizados silenciosamente.

---

## 8. Pontos de Atenção

- [ ] **Datas hardcoded em 5 queries:** `>= '2025-07-01'` (Expedido), `BETWEEN '2026-01-01' AND '2026-02-28'` (posição atual), `>= '2026-01-01'` (evolucao_saldo, entrada_saida, estoque_raw) — atualizar periodicamente
- [ ] **6 relacionamentos N:N** — testar visuais com filtros cruzados
- [ ] **Dependência do ETL N8N** — falha no ETL silencia o dashboard sem alertas
- [ ] **IP hardcoded** (`10.201.100.201`) — não funciona fora da rede interna sem VPN/gateway
- [ ] **`REPLACE(campo, ',', '.')::numeric`** em múltiplas queries — indica que valores numéricos estão armazenados como texto com vírgula decimal no banco. Considerar corrigir na origem
- [ ] **`Valor Produzido 2`** usa coluna `Custo Ajustado` — verificar de onde vem esse ajuste e documentar a regra
- [ ] **Três versões de "Valor Produzido"** (`Custo Original`, `2`, `Real`) — clarificar qual é usada em produção e qual é experimental

---

## 9. Histórico de Alterações

| Data | O que mudou | Quem |
|---|---|---|
| 2026-01-15 | Criação inicial (A Expedir, Expedido) | — |
| 2026-02-05 | Adição de filtro de data em Expedido | — |
| 2026-03-03 | Adição do módulo de estoque (fato_posicao_atual, evolucao_saldo, entrada_saida, estoque_raw) | — |
| 2026-03-16 | Integração com tabelas Belga ETL (Consumo SQL, Produtos PK, Composição KIT, PRE_ROMANEIO, Composicao) | — |
| 2026-03-23 | Documentação técnica completa gerada via MCP | André |
