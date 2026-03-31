# 📊 TONELADA_VENDA_PRODUZIDA — Documentação Técnica

> **Notion:** _[adicionar link da entrada no catálogo]_
> **Power BI Service:** https://app.powerbi.com/groups/b0090161-5335-49fa-a00c-68ff4b319e1f/reports/eac35970-68cb-4ca5-bbdf-ab4c8d34dce9/036491b6297c091961d1?experience=power-bi
> **Última atualização:** 2026-03-23
> **Responsável:** André

---

## 1. Objetivo

Dashboard industrial para acompanhamento de **tonelagem movimentada vs. metas** por unidade e tipo de produto. Suporta decisões operacionais e táticas da área Industrial sobre performance de produção e expedição.

- **Quem usa:** Gestão Industrial / Diretoria
- **Frequência de consulta:** Operacional (diário/semanal)
- **Métricas centrais:** Total Movimentado (t), HVA (t), CHAPA (t), % Meta Atingida

---

## 2. Fontes de Dados

Todas as tabelas são **Import** via arquivos Excel (.xlsx) locais. Não há conexão direta com banco de dados.

| Tabela | Tipo | Arquivo de Origem | Caminho |
|---|---|---|---|
| `BASE` | Import / M | `RESUMO 2 ANOS CHAPAS (CORRIGIDO) final.xlsx` | `C:\Users\andre\OneDrive\...\Alumiação\Toneladas\` |
| `CONSUMIDO` | Import / M | `consumido_tempera.xlsx` | `C:\Users\andre\OneDrive\...\Alumiação\Toneladas\` |
| `EXPEDIDO` | Import / M | `venda_chaparia260119-074000.xlsx` | `C:\Users\andre\OneDrive\...\Alumiação\Toneladas\` |
| `METAS` | Import / M | `METAS.xlsx` | `C:\Users\andre\OneDrive\...\Alumiação\Toneladas\` |
| `DIM_PRODUTOS` | Import / M | `RESUMO 2 ANOS CHAPAS (CORRIGIDO) final.xlsx` | `C:\Users\andre\Downloads\` ⚠️ |
| `DIM_TIPO` | Import / M | `RESUMO 2 ANOS CHAPAS (CORRIGIDO) final.xlsx` | `C:\Users\andre\Downloads\` ⚠️ |
| `correcao` | Import / M | `correcao.xlsx` | `C:\Users\andre\Downloads\` ⚠️ |
| `CORRECAO_TEMPER` | Import / M | Tabela embutida (Base64+Deflate inline) | — |
| `DIM_TIPO_APRESENTACAO` | Calculated (DAX) | Tabela calculada | — |
| `DIM_ORDEM_TIPO` | Calculated (DAX) | Tabela calculada | — |
| `DIM_TIPO_LOJA` | Calculated (DAX) | Tabela calculada | — |

> ⚠️ `DIM_PRODUTOS`, `DIM_TIPO` e `correcao` leem de `Downloads` — pasta temporária. Mover para `OneDrive\...\Alumiação\Toneladas\`.
> ⚠️ `BASE` e `DIM_PRODUTOS` leem o mesmo arquivo (`RESUMO 2 ANOS CHAPAS...`) de caminhos diferentes. Unificar.

---

## 3. Queries Power Query (M) — Completas

### 3.1 BASE

```m
let
    Fonte = Excel.Workbook(File.Contents("C:\Users\andre\OneDrive\Documentos\Development\Alumiação\Toneladas\RESUMO 2 ANOS CHAPAS (CORRIGIDO) final.xlsx"), null, true),
    Sheet_Sheet = Fonte{[Item="Sheet",Kind="Sheet"]}[Data],
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(Sheet_Sheet, [PromoteAllScalars=true]),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Cabeçalhos Promovidos",{{"unidade", type text}, {"DS_OES", type text}, {"DS_CAT", type text}, {"DS_PRO", type text}, {"DS_SCP", type text}, {"m2", type number}, {"ANO", type any}, {"MES", Int64.Type}, {"PESO UN", type number}, {"PESO", type number}, {"TIPO", type text}}),
    #"Linhas Classificadas" = Table.Sort(#"Tipo Alterado",{{"unidade", Order.Descending}})
in
    #"Linhas Classificadas"
```

### 3.2 CONSUMIDO
> Normaliza nomes de unidades, constrói chaves compostas `unidade|produto|subclasse`, faz join com `DIM_PRODUTOS` para enriquecer com PESO UN e TIPO. Fallback: TIPO nulo → "FLOAT", PESO UN nulo → 20.

```m
let
    Fonte = Excel.Workbook(File.Contents("C:\Users\andre\OneDrive\Documentos\Development\Alumiação\Toneladas\consumido_tempera.xlsx"), null, true),
    Sheet1_Sheet = Fonte{[Item="Sheet1",Kind="Sheet"]}[Data],
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Cabeçalhos Promovidos",{{"unidade", type text}, {"quantidade", Int64.Type}, {"nome_produto", type text}, {"categoria", type text}, {"classe", type text}, {"subclasse", type text}, {"cod_produto", type text}}),
    #"Personalização Adicionada" = Table.AddColumn(#"Tipo Alterado", "chavE_PRODUTO", each Text.Trim([unidade]) & "|" & Text.Trim([nome_produto]) & "|" & Text.Trim([subclasse])),
    #"Texto Limpo" = Table.TransformColumns(#"Personalização Adicionada",{{"nome_produto", Text.Clean, type text}, {"chavE_PRODUTO", Text.Clean, type text}, {"subclasse", Text.Clean, type text}}),
    #"Valor Substituído"  = Table.ReplaceValue(#"Texto Limpo","4D Vidros","4D VIDROS",Replacer.ReplaceText,{"unidade"}),
    #"Valor Substituído1" = Table.ReplaceValue(#"Valor Substituído","ALAGOAS VIDROS","ALAGOAS",Replacer.ReplaceText,{"unidade"}),
    #"Linhas Classificadas" = Table.Sort(#"Valor Substituído1",{{"unidade", Order.Ascending}}),
    #"Valor Substituído2" = Table.ReplaceValue(#"Linhas Classificadas","ALLGLASS TEMPERA","ALLGLASS",Replacer.ReplaceText,{"unidade"}),
    #"Valor Substituído3" = Table.ReplaceValue(#"Valor Substituído2","INBRAVIDROS","IMBRAVIDROS",Replacer.ReplaceText,{"unidade"}),
    #"Valor Substituído4" = Table.ReplaceValue(#"Valor Substituído3","Oazem","OAZEM",Replacer.ReplaceText,{"unidade"}),
    #"Valor Substituído5" = Table.ReplaceValue(#"Valor Substituído4","VITORIA DE SANTO ANTAO","VITORIA",Replacer.ReplaceText,{"unidade"}),
    #"Valor Substituído6" = Table.ReplaceValue(#"Valor Substituído5","UBERVIDROS","UBERABA",Replacer.ReplaceText,{"unidade"}),
    #"Personalização Adicionada1" = Table.AddColumn(#"Valor Substituído6", "chave_produto_2", each Text.Trim([unidade]) & "|" & Text.Trim([nome_produto]) & "|" & Text.Trim([subclasse])),
    #"Consultas Mescladas" = Table.NestedJoin(#"Personalização Adicionada1", {"chave_produto_2"}, DIM_PRODUTOS, {"chave_produto"}, "DIM_PRODUTOS", JoinKind.LeftOuter),
    #"DIM_PRODUTOS Expandido" = Table.ExpandTableColumn(#"Consultas Mescladas", "DIM_PRODUTOS", {"PESO UN", "TIPO"}, {"PESO UN", "TIPO"}),
    #"Personalização Adicionada2" = Table.AddColumn(#"DIM_PRODUTOS Expandido", "key_tipo", each [unidade] & "|" & [TIPO]),
    #"Valor Substituído7" = Table.ReplaceValue(#"Personalização Adicionada2",null,"FLOAT",Replacer.ReplaceValue,{"TIPO"}),
    #"Valor Substituído8" = Table.ReplaceValue(#"Valor Substituído7",null,20,Replacer.ReplaceValue,{"PESO UN"}),
    #"Personalização Adicionada3" = Table.AddColumn(#"Valor Substituído8", "key_tipo2", each [unidade] & "|" & [TIPO]),
    #"Colunas Removidas" = Table.RemoveColumns(#"Personalização Adicionada3",{"key_tipo"}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Colunas Removidas",{{"key_tipo2", "key_tipo"}}),
    #"Linhas Classificadas1" = Table.Sort(#"Colunas Renomeadas",{{"unidade", Order.Descending}}),
    #"Valor Substituído9" = Table.ReplaceValue(#"Linhas Classificadas1","04+04MM","08mm",Replacer.ReplaceText,{"subclasse"}),
    #"Coluna Condicional Adicionada" = Table.AddColumn(#"Valor Substituído9", "subtipo_mapeado", each if [TIPO] = "FLOAT" then "TEMPERADO" else [TIPO]),
    #"Personalização Adicionada4" = Table.AddColumn(#"Coluna Condicional Adicionada", "key_sub", each [unidade] & "|" & [TIPO] & "|" & [subtipo_mapeado])
in
    #"Personalização Adicionada4"
```

### 3.3 EXPEDIDO
> Normaliza unidades (inclui typos históricos: ORAZEM→OAZEM, ALLGASS→ALLGLASS). Join com `DIM_PRODUTOS` e depois com `correcao` — `correcao` tem prioridade para sobrescrever PESO UN e TIPO. `subtipo_mapeado`: FLOAT → "CHAPARIA".

```m
let
    Fonte = Excel.Workbook(File.Contents("C:\Users\andre\OneDrive\Documentos\Development\Alumiação\Toneladas\venda_chaparia260119-074000.xlsx"), null, true),
    Sheet1_Sheet = Fonte{[Item="Sheet1",Kind="Sheet"]}[Data],
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Cabeçalhos Promovidos",{{"Tipo_Unidade", type text}, {"Unidade", type text}, {"DS_OES", type text}, {"DS_CAT", type text}, {"DS_PRO", type text}, {"DS_SCP", type text}, {"m2", type number}, {"ANO", Int64.Type}, {"MES", Int64.Type}}),
    #"Personalização Adicionada" = Table.AddColumn(#"Tipo Alterado", "Personalizar", each Text.Trim([Unidade]) & "|" & Text.Trim([DS_PRO]) & "|" & Text.Trim([DS_SCP])),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Personalização Adicionada",{{"Personalizar", "chave_produto"}}),
    #"Texto Limpo" = Table.TransformColumns(#"Colunas Renomeadas",{{"chave_produto", Text.Clean, type text}, {"DS_PRO", Text.Clean, type text}}),
    -- Normalização de unidades:
    #"Valor Substituído"  = Table.ReplaceValue(#"Texto Limpo","4D Vidros","4D VIDROS",Replacer.ReplaceText,{"Unidade"}),
    #"Valor Substituído1" = Table.ReplaceValue(#"Valor Substituído","ALAGOAS VIDROS","ALAGOAS",Replacer.ReplaceText,{"Unidade"}),
    #"Valor Substituído2" = Table.ReplaceValue(#"Valor Substituído1","ALLGLASS TEMPERA","ALLGASS",Replacer.ReplaceText,{"Unidade"}),  -- typo intermediário
    #"Valor Substituído3" = Table.ReplaceValue(#"Valor Substituído2","GM Recife","GM RECIFE",Replacer.ReplaceText,{"Unidade"}),
    #"Valor Substituído4" = Table.ReplaceValue(#"Valor Substituído3","INBRAVIDROS","IMBRAVIDROS",Replacer.ReplaceText,{"Unidade"}),
    #"Valor Substituído5" = Table.ReplaceValue(#"Valor Substituído4","Oazem","ORAZEM",Replacer.ReplaceText,{"Unidade"}),             -- typo intermediário
    #"Valor Substituído6" = Table.ReplaceValue(#"Valor Substituído5","ORAZEM","OAZEM",Replacer.ReplaceText,{"Unidade"}),             -- correção final
    #"Valor Substituído7" = Table.ReplaceValue(#"Valor Substituído6","VITORIA DE SANTO ANTAO","VITORIA",Replacer.ReplaceText,{"Unidade"}),
    #"Linhas Classificadas" = Table.Sort(#"Valor Substituído7",{{"Unidade", Order.Ascending}}),
    #"Valor Substituído8" = Table.ReplaceValue(#"Linhas Classificadas","ALLGASS","ALLGLASS",Replacer.ReplaceText,{"Unidade"}),       -- correção final
    #"Personalização Adicionada1" = Table.AddColumn(#"Valor Substituído8", "chave_produto_2", each Text.Trim([Unidade]) & "|" & Text.Trim([DS_PRO]) & "|" & Text.Trim([DS_SCP])),
    #"Texto Limpo1" = Table.TransformColumns(#"Personalização Adicionada1",{{"chave_produto_2", Text.Clean, type text}, {"Unidade", Text.Clean, type text}}),
    -- Join 1: DIM_PRODUTOS (fonte primária de PESO UN e TIPO)
    #"Consultas Mescladas" = Table.NestedJoin(#"Texto Limpo1", {"chave_produto_2"}, DIM_PRODUTOS, {"chave_produto"}, "DIM_PRODUTOS", JoinKind.LeftOuter),
    #"DIM_PRODUTOS Expandido" = Table.ExpandTableColumn(#"Consultas Mescladas", "DIM_PRODUTOS", {"PESO UN", "TIPO"}, {"DIM_PRODUTOS.PESO UN", "DIM_PRODUTOS.TIPO"}),
    -- Join 2: correcao (sobrescreve DIM_PRODUTOS quando presente)
    #"Consultas Mescladas1" = Table.NestedJoin(#"DIM_PRODUTOS Expandido", {"chave_produto_2"}, correcao, {"chave_produto_2"}, "correcao", JoinKind.LeftOuter),
    #"correcao Expandido" = Table.ExpandTableColumn(#"Consultas Mescladas1", "correcao", {"PESO UN", "TIPO"}, {"PESO UN", "TIPO"}),
    -- Mapeamento final: correcao tem prioridade
    #"Personalização Adicionada3" = Table.AddColumn(#"correcao Expandido", "PESOUN_MAPEADO", each if [DIM_PRODUTOS.PESO UN] <> null then [DIM_PRODUTOS.PESO UN] else [PESO UN]),
    #"Personalização Adicionada4" = Table.AddColumn(#"Personalização Adicionada3", "TIPO_MAPEADO", each if [DIM_PRODUTOS.TIPO] <> null then [DIM_PRODUTOS.TIPO] else [TIPO]),
    #"Personalização Adicionada5" = Table.AddColumn(#"Personalização Adicionada4", "key_product", each Text.Trim([Unidade]) & "|" & Text.Trim([DS_PRO]) & "|" & Text.Trim([DS_SCP])),
    #"Colunas Renomeadas1" = Table.RenameColumns(#"Personalização Adicionada5",{{"Column11", "tonelada"}}),
    #"Personalização Adicionada6" = Table.AddColumn(#"Colunas Renomeadas1", "Personalizar", each [Unidade] & "|" & [TIPO_MAPEADO]),
    #"Colunas Renomeadas2" = Table.RenameColumns(#"Personalização Adicionada6",{{"Personalizar", "key_tipo"}}),
    #"Tipo Alterado1" = Table.TransformColumnTypes(#"Colunas Renomeadas2",{{"tonelada", type number}}),
    #"Valor Substituído9" = Table.ReplaceValue(#"Tipo Alterado1",null,"FLOAT",Replacer.ReplaceValue,{"TIPO_MAPEADO"}),
    #"Colunas Renomeadas3" = Table.RenameColumns(#"Valor Substituído9",{{"key_tipo", "TIPO_KEY"}}),
    #"Personalização Adicionada7" = Table.AddColumn(#"Colunas Renomeadas3", "key_tipo", each [Unidade] & "|" & [TIPO_MAPEADO]),
    -- unidade_unificada: agrupa unidades relacionadas para exibição consolidada
    #"Personalização Adicionada8" = Table.AddColumn(#"Personalização Adicionada7", "unidade_unificada", each
        if List.Contains({"4D VIDROS","GM Salvador","GMFEIRA","BARROSREIS"}, [Unidade]) then "4D VIDROS / GM Salvador / GMFEIRA / BARROSREIS"
        else if List.Contains({"IMBRAVIDROS","IRECE","GM JUAZEIRO"}, [Unidade]) then "IMBRAVIDROS / IRECE / GM JUAZEIRO"
        else if List.Contains({"Alumiaco Recife","OLINDA"}, [Unidade]) then "Alumiaco Recife / OLINDA"
        else [Unidade]),
    #"Texto Limpo2" = Table.TransformColumns(#"Personalização Adicionada8",{{"Unidade", Text.Clean, type text}}),
    #"Linhas Classificadas1" = Table.Sort(#"Texto Limpo2",{{"Tipo_Unidade", Order.Descending}, {"Unidade", Order.Descending}}),
    -- Correções de UBERVIDROS → UBERABA em todas as colunas relevantes (key_tipo, key_product, chave_produto_2)
    #"Valor Substituído10" = Table.ReplaceValue(#"Linhas Classificadas1","UBERVIDROS","UBERABA",Replacer.ReplaceText,{"Unidade"}),
    -- ... (substituições adicionais nas chaves compostas para manter consistência)
    #"Coluna Condicional Adicionada" = Table.AddColumn(#"Valor Substituído29", "subtipo_mapeado", each if [TIPO_MAPEADO] = "FLOAT" then "CHAPARIA" else [TIPO_MAPEADO]),
    #"Personalização Adicionada9" = Table.AddColumn(#"Coluna Condicional Adicionada", "Personalizar", each [Unidade] & "|" & [TIPO_MAPEADO] & "|" & [subtipo_mapeado]),
    #"Colunas Renomeadas4" = Table.RenameColumns(#"Personalização Adicionada9",{{"Personalizar", "key_sub"}})
in
    #"Colunas Renomeadas4"
```

### 3.4 METAS

```m
let
    Fonte = Excel.Workbook(File.Contents("C:\Users\andre\OneDrive\Documentos\Development\Alumiação\Toneladas\METAS.xlsx"), null, true),
    Planilha1_Sheet = Fonte{[Item="Planilha1",Kind="Sheet"]}[Data],
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(Planilha1_Sheet, [PromoteAllScalars=true]),
    #"Personalização Adicionada" = Table.AddColumn(#"Cabeçalhos Promovidos", "Personalizar", each [UNIDADE] & "|" & [TIPO]),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Personalização Adicionada",{{"META", "Meta (ton)"}}),
    -- TIPO_MACRO: agrupa TEMPERADO e CHAPARIA como "FLOAT" para alinhar com hierarquia de EXPEDIDO
    #"Coluna Condicional Adicionada" = Table.AddColumn(#"Colunas Renomeadas", "TIPO_MACRO", each
        if [TIPO] = "TEMPERADO" then "FLOAT"
        else if [TIPO] = "CHAPARIA" then "FLOAT"
        else [TIPO]),
    #"Colunas Renomeadas1" = Table.RenameColumns(#"Coluna Condicional Adicionada",{{"TIPO", "subtipo_mapeado"}}),
    #"Personalização Adicionada1" = Table.AddColumn(#"Colunas Renomeadas1", "key_sub", each [UNIDADE] & "|" & [TIPO_MACRO] & "|" & [subtipo_mapeado]),
    #"Tipo Alterado1" = Table.TransformColumnTypes(#"Personalização Adicionada1",{{"Meta (ton)", type number}})
in
    #"Tipo Alterado1"
```

### 3.5 DIM_PRODUTOS

```m
let
    Fonte = Excel.Workbook(File.Contents("C:\Users\andre\Downloads\RESUMO 2 ANOS CHAPAS (CORRIGIDO) final.xlsx"), null, true),
    Sheet_Sheet = Fonte{[Item="Sheet",Kind="Sheet"]}[Data],
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(Sheet_Sheet, [PromoteAllScalars=true]),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Cabeçalhos Promovidos",{{"unidade", type text}, {"DS_OES", type text}, {"DS_CAT", type text}, {"DS_PRO", type text}, {"DS_SCP", type text}, {"m2", type number}, {"ANO", type any}, {"MES", Int64.Type}, {"PESO UN", type number}, {"PESO", type number}, {"TIPO", type text}}),
    #"Colunas Removidas" = Table.RemoveColumns(#"Tipo Alterado",{"DS_OES", "m2", "ANO", "MES", "PESO"}),
    #"Personalização Adicionada" = Table.AddColumn(#"Colunas Removidas", "Personalizar", each Text.Trim([unidade]) & "|" & Text.Trim([DS_PRO]) & "|" & Text.Trim([DS_SCP])),
    #"Texto Limpo1" = Table.TransformColumns(#"Personalização Adicionada",{{"Personalizar", Text.Clean, type text}}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Texto Limpo1",{{"Personalizar", "chave_produto"}}),
    #"Texto Limpo" = Table.TransformColumns(#"Colunas Renomeadas",{{"unidade", Text.Clean, type text}, {"DS_PRO", Text.Clean, type text}}),
    #"Duplicatas Removidas" = Table.Distinct(#"Texto Limpo", {"unidade", "DS_PRO", "DS_SCP"}),
    #"Linhas Filtradas" = Table.SelectRows(#"Duplicatas Removidas", each ([DS_SCP] <> null)),
    #"Personalização Adicionada1" = Table.AddColumn(#"Linhas Filtradas", "Personalizar", each [unidade] & "|" & [TIPO]),
    #"Texto Limpo2" = Table.TransformColumns(#"Personalização Adicionada1",{{"chave_produto", Text.Clean, type text}})
in
    #"Texto Limpo2"
```

### 3.6 DIM_TIPO

```m
let
    -- Mesma origem que DIM_PRODUTOS (Downloads ⚠️)
    -- Após deduplicar, remove colunas desnecessárias e combina com CORRECAO_TEMPER
    #"Consulta Acrescentada" = Table.Combine({#"Personalização Adicionada2", CORRECAO_TEMPER}),
    -- TIPO nulo → "FLOAT"
    -- Personalizar nulo → "TEMPER PATOS|FLOAT"
    -- unidade_unificada "" → "VITORIA"
    -- subtipo_mapeado: se subtipo existir usa subtipo, senão usa TIPO
    #"Coluna Condicional Adicionada" = Table.AddColumn(#"Valor Substituído2", "subtipo_mapeado", each if [subtipo] = null then [TIPO] else [subtipo]),
    #"Colunas Removidas2" = Table.RemoveColumns(#"Coluna Condicional Adicionada",{"subtipo"}),
    #"Personalização Adicionada3" = Table.AddColumn(#"Colunas Removidas2", "key_sub", each [unidade] & "|" & [TIPO] & "|" & [subtipo_mapeado])
in
    #"Personalização Adicionada3"
```

### 3.7 correcao

```m
let
    Fonte = Excel.Workbook(File.Contents("C:\Users\andre\Downloads\correcao.xlsx"), null, true),
    correcao_Sheet = Fonte{[Item="correcao",Kind="Sheet"]}[Data],
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(correcao_Sheet, [PromoteAllScalars=true]),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Cabeçalhos Promovidos",{{"unidade", type text}, {"DS_PRO", type text}, {"chave_produto_2", type text}, {"PESO UM", type number}, {"TIPO", type text}}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Tipo Alterado",{{"PESO UM", "PESO UN"}})
in
    #"Colunas Renomeadas"
```

### 3.8 CORRECAO_TEMPER
> Dados embutidos diretamente no modelo em Base64+Deflate. Não depende de arquivo externo. Corrige entrada "4D VIDROS|FLOT" → "4D VIDROS|FLOAT". Para atualizar é necessário editar o Power Query diretamente.

---

## 4. Modelo de Dados

### Relacionamentos

| De (Tabela) | De (Coluna) | Para (Tabela) | Para (Coluna) | Cardinalidade | Filtro Cruzado | Ativo |
|---|---|---|---|---|---|---|
| CONSUMIDO | chave_produto_2 | DIM_PRODUTOS | chave_produto | N:1 | BothDirections | ✅ |
| CONSUMIDO | unidade | EXPEDIDO | Unidade | **N:N** ⚠️ | BothDirections | ✅ |
| CONSUMIDO | key_sub | DIM_TIPO | key_sub | N:1 | OneDirection | ✅ |
| EXPEDIDO | key_sub | DIM_TIPO | key_sub | N:1 | OneDirection | ✅ |
| METAS | key_sub | DIM_TIPO | key_sub | N:1 | OneDirection | ✅ |
| DIM_TIPO | TIPO | DIM_ORDEM_TIPO | TIPO | N:1 | OneDirection | ✅ |
| DIM_TIPO_LOJA | tipo | EXPEDIDO | TIPO_MAPEADO | **N:N** ⚠️ | BothDirections | ✅ |
| EXPEDIDO | TIPO_KEY | METAS | Personalizar | **N:N** ⚠️ | BothDirections | ✅ |

### Diagrama simplificado

```
DIM_ORDEM_TIPO
      ↑ N:1 (OneDir)
   DIM_TIPO ←── N:1 (OneDir) ── CONSUMIDO ──── N:1 (Both) ──→ DIM_PRODUTOS
      ↑ N:1 (OneDir)                 ↕ N:N (Both)
   EXPEDIDO ←── N:N (Both) ── DIM_TIPO_LOJA
      ↕ N:N (Both)
    METAS

Calculadas (sem relacionamento direto com fatos):
  DIM_TIPO_APRESENTACAO  → seletor de tipo nos visuais
  DIM_ORDEM_TIPO         → ordenação dos tipos
```

---

## 5. Medidas DAX — Completas (21 medidas)

### 5.1 Tabela: CONSUMIDO (7 medidas)

#### Qtd Consumida
```dax
Qtd Consumida = SUM ( CONSUMIDO[quantidade] )
```

#### Peso Unitário (kg)
```dax
Peso Unitário (kg) = MAX ( DIM_PRODUTOS[PESO UN] )
```

#### Tonelada Consumida (t)
```dax
Tonelada Consumida (t) = SUM ( CONSUMIDO[ton_consumida] )
```

#### Total Movimentado (t)
> Medida central. COALESCE garante que nulos sejam tratados como zero.
```dax
Total Movimentado (t) =
COALESCE ( [Peso Expedido (t)], 0 )
+ COALESCE ( [Tonelada Consumida (t)], 0 )
```

#### HVA (t)
> Alto Valor Agregado: tipos LAMINADO, ESPELHO, REFLETIVO, PINTADO.
```dax
HVA (t) =
CALCULATE (
    [Total Movimentado (t)],
    KEEPFILTERS (
        DIM_TIPO[TIPO] IN {
            "LAMINADO",
            "ESPELHO",
            "REFLETIVO",
            "PINTADO"
        }
    )
)
```

#### CHAPA (t)
```dax
CHAPA (t) =
CALCULATE (
    [Total Movimentado (t)],
    KEEPFILTERS (
        DIM_TIPO[TIPO] IN { "FLOAT" }
    )
)
```

#### Debug Peso UN
> Medida de diagnóstico. Conta linhas de EXPEDIDO sem PESO UN. Avaliar remoção/ocultação.
```dax
Debug Peso UN =
COUNTROWS(
    FILTER(
        EXPEDIDO,
        ISBLANK(EXPEDIDO[PESO UN])
    )
)
```

---

### 5.2 Tabela: EXPEDIDO (1 medida)

#### Peso Expedido (t)
```dax
Peso Expedido (t) = SUM ( EXPEDIDO[tonelada] )
```

---

### 5.3 Tabela: METAS (12 medidas)

#### Meta 1 (t)
> SUMX + VALUES por key_sub evita dupla contagem.
```dax
Meta 1 (t) =
SUMX(
    VALUES ( DIM_TIPO[key_sub] ),
    CALCULATE ( MAX ( METAS[Meta (ton)] ) )
)
```

#### Meta 1 (t) – FLOAT por unidade
> Exclui metas FLOAT para unidades sem produção de chapa. Lista hardcoded.
```dax
Meta 1 (t) – FLOAT por unidade =
VAR UnidadesSemFLOAT =
{
    "VITORIA", "UBERABA", "TEMPER PATOS", "ALAGOAS",
    "ALLGLASS", "BRASILIA", "OAZEM", "FORTALEZA",
    "IMBRAVIDROS", "4D VIDROS"
}
RETURN
SUMX (
    FILTER (
        METAS,
        NOT (
            METAS[tipo_macro] = "FLOAT"
                && METAS[subtipo_mapeado] = "FLOAT"
                && METAS[unidade] IN UnidadesSemFLOAT
        )
    ),
    METAS[Meta (ton)]
)
```

#### Meta 1 (ton) - Lojas
> Remove filtro de EXPEDIDO para visuais de lojas/bodinhos.
```dax
Meta 1 (ton) - Lojas =
CALCULATE (
    [Meta 1 (t)],
    REMOVEFILTERS ( EXPEDIDO )
)
```

#### Meta 2 (t)
```dax
Meta 2 (t) =
SUMX(
    VALUES ( DIM_TIPO[key_sub] ),
    CALCULATE ( MAX ( METAS[META 2] ) )
)
```

#### Meta 2 (t) – FLOAT por unidade
```dax
Meta 2 (t) – FLOAT por unidade =
VAR UnidadesSemFLOAT =
{
    "VITORIA", "UBERABA", "TEMPER PATOS", "ALAGOAS",
    "ALLGLASS", "BRASILIA", "OAZEM", "FORTALEZA",
    "IMBRAVIDROS", "4D VIDROS"
}
RETURN
SUMX (
    FILTER (
        METAS,
        NOT (
            METAS[tipo_macro] = "FLOAT"
                && METAS[subtipo_mapeado] = "FLOAT"
                && METAS[unidade] IN UnidadesSemFLOAT
        )
    ),
    METAS[Meta 2 (t)]
)
```

#### Meta HVA (t)
```dax
Meta HVA (t) =
CALCULATE (
    SUM ( METAS[Meta (ton)] ),
    KEEPFILTERS (
        METAS[tipo_macro] IN {
            "LAMINADO", "ESPELHO", "REFLETIVO", "PINTADO"
        }
    )
)
```

#### Meta 2 HVA (t)
```dax
Meta 2 HVA (t) =
CALCULATE (
    SUM ( METAS[META 2] ),
    KEEPFILTERS (
        METAS[tipo_macro] IN {
            "LAMINADO", "ESPELHO", "REFLETIVO", "PINTADO"
        }
    )
)
```

#### % Meta Atingida
```dax
% Meta Atingida =
DIVIDE(
    [Peso Expedido (t)],
    [Meta 1 (ton) - Lojas]
)
```

#### % Meta Total Movimentado
```dax
% Meta Total Movimentado =
DIVIDE(
    [Total Movimentado (t)],
    [Meta 1 (t) – FLOAT por unidade]
)
```

#### % Meta Total Movimentado 2
```dax
% Meta Total Movimentado 2 =
DIVIDE(
    [Total Movimentado (t)],
    [Meta 2 (t) – FLOAT por unidade]
)
```

#### % Atingido HVA
```dax
% Atingido HVA =
DIVIDE (
    [HVA (t)],
    [Meta HVA (t)]
)
```

#### % Atingido 2 HVA
```dax
% Atingido 2 HVA =
DIVIDE (
    [HVA (t)],
    [Meta 2 HVA (t)]
)
```

---

### 5.4 Tabela: DIM_TIPO_APRESENTACAO (1 medida)

#### Total Movimentado (t) - Visual
> ⛔ **ERRO ATIVO (SemanticError)** — coluna `tipo_analitico` não existe em CONSUMIDO nem EXPEDIDO.
> Substituir por `subtipo_mapeado` ou `TIPO_MAPEADO` conforme a intenção original.

```dax
Total Movimentado (t) - Visual =
VAR TipoSel = SELECTEDVALUE ( DIM_TIPO_APRESENTACAO[Tipo_Visual] )

RETURN
SWITCH (
    TRUE (),
    TipoSel = "FLOAT",
        CALCULATE ( [Total Movimentado (t)], CONSUMIDO[tipo_analitico] = "TEMPERADO" )    -- ⛔ coluna inexistente
        + CALCULATE ( [Total Movimentado (t)], EXPEDIDO[tipo_analitico] = "CHAPARIA" ),   -- ⛔ coluna inexistente
    TipoSel = "TEMPERADO",
        CALCULATE ( [Total Movimentado (t)], CONSUMIDO[tipo_analitico] = "TEMPERADO" ),   -- ⛔ coluna inexistente
    TipoSel = "CHAPARIA",
        CALCULATE ( [Total Movimentado (t)], EXPEDIDO[tipo_analitico] = "CHAPARIA" ),     -- ⛔ coluna inexistente
    CALCULATE ( [Total Movimentado (t)], DIM_TIPO[TIPO] = TipoSel )
)
```

---

## 6. Atualização e Refresh

| Campo | Valor |
|---|---|
| Tipo | Import (todas as tabelas) |
| Modo atual | Manual — abrir .pbix e clicar em Atualizar |
| Gateway | Não configurado (arquivo local) |
| Dataset no Service | _[preencher após publicação]_ |

> Para refresh automático no Power BI Service: configurar **gateway de dados local** na máquina do André apontando para os arquivos no OneDrive.

---

## 7. Pontos de Atenção

- [ ] **⛔ ERRO ATIVO** — `Total Movimentado (t) - Visual` referencia `tipo_analitico` inexistente. Corrigir antes de publicar.
- [ ] **Caminhos divergentes:** `BASE` e `DIM_PRODUTOS` leem o mesmo arquivo de pastas diferentes (`OneDrive` vs `Downloads`). Unificar.
- [ ] **`DIM_PRODUTOS`, `DIM_TIPO`, `correcao`** em `Downloads` — mover para `OneDrive\...\Alumiação\Toneladas\`.
- [ ] **Lista `UnidadesSemFLOAT` hardcoded** em 2 medidas — manter atualizada a cada nova unidade.
- [ ] **3 relacionamentos N:N** — testar visuais com filtros cruzados para verificar dupla contagem.
- [ ] **`Debug Peso UN`** — medida de diagnóstico, ocultar ou remover antes de publicar.
- [ ] **`CORRECAO_TEMPER`** com dados embutidos — qualquer atualização exige editar o Power Query manualmente.
- [ ] **`Meta 2` e `% Meta Total Movimentado 2`** — verificar se estão em uso nos visuais e documentar.

---

## 8. Histórico de Alterações

| Data | O que mudou | Quem |
|---|---|---|
| 2026-01-19 | Criação inicial do modelo | — |
| 2026-01-21 | Adição de Meta 2 e lógica SUMX por key_sub | — |
| 2026-02-11 | HVA, CHAPA, metas HVA, medida Visual, CORRECAO_TEMPER | — |
| 2026-03-11 | Recálculo geral das medidas de Meta | — |
| 2026-03-23 | Documentação técnica completa gerada via MCP | André |
