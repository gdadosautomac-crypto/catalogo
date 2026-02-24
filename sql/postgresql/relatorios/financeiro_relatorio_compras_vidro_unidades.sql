-- Nome: financeiro_relatorio_compras_vidro_unidades.sql
-- Banco: PostgreSQL
-- Tipo: Relatório Final
-- Utilização: Script Python (Exportação Excel)
-- Área: Diretoria
-- Descrição: Gera relatório consolidado de pedidos de compra de vidro por unidade com valor, metragem e tonelada
-- Autor: André Machado
-- Data Criação: 2026-02
-- Status: Ativo

SELECT
  pc.fornecedor,
  pc.unidade AS unidade_destino,
  pc.pedido,
  pc.cod_produto,
  pr.nome_produto,
  pr.subclasse,
  pr.fabricante,
  pc.data_pedido::timestamp AS data_pedido,
  REPLACE(pc.qtd_comprada, ',', '.')::numeric AS qtd_comprada,
  -- 💰 valor correto
  pc.valor_pago::numeric AS valor_pago,
  -- ⭐ nº itens do pedido
  COUNT(*) OVER (
  PARTITION BY pc.unidade, pc.pedido
) AS qtd_itens_pedido,
  -- ⭐ valor dividido correto
  ROUND(
  pc.valor_pago::numeric
    / COUNT(*) OVER (
        PARTITION BY pc.unidade, pc.pedido
      ),
  2
) AS valor_dividido,
  REPLACE(pr.m2, ',', '.')::numeric   AS m2_produto,
  REPLACE(pr.peso, ',', '.')::numeric AS peso_produto
FROM pedidos_compras pc
LEFT JOIN produtos_completos pr
  ON pc.cod_produto = pr.codigo_produto and pc.unidade = pr.unidade
WHERE pc.data_pedido::timestamp >= DATE '2026-01-01'
  AND pc.data_pedido::timestamp <  DATE '2026-02-24' and pc.tipo_unidade = 'Tempera' and pc.valor_pago is not null
ORDER BY
  pc.unidade,
  pc.fornecedor,
  pc.pedido,
  pc.cod_produto;