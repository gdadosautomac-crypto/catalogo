# 📊 Gestão de Dados & Automação

Repositório oficial do setor de Dados & Automação do grupo Marcolan.

Este repositório centraliza todos os ativos técnicos relacionados a:

- 🧱 ETL e Data Warehouse (Pentaho)
- 🗄 Consultas SQL (PostgreSQL e MySQL)
- 🤖 Automações (N8N)
- 📊 Dashboards Power BI
- 🌐 Aplicações Lovable (Portais e CRM)
- 🐍 Scripts auxiliares
- 🔐 Documentação técnica de credenciais (sem segredos)

---

# 🎯 Objetivo

Garantir:

- Organização técnica
- Versionamento adequado
- Continuidade operacional
- Padronização de desenvolvimento
- Redução de dependência individual
- Governança e rastreabilidade

Este repositório é privado e pertence exclusivamente ao setor.

---

# 🏗 Estrutura do Repositório

```
dados-automacao-grupo/
│
├── docs/
│
├── sql/
│ ├── postgresql/
│ │ ├── base-estrutural/
│ │ ├── relatorios/
│ │ └── apoio-n8n/
│ │
│ └── mysql/
│ ├── operacionais/
│ └── relatorios-diretoria/
│
├── pentaho/
│ ├── transformations/
│ └── jobs/
│
├── n8n/
│ └── workflows/
│
├── powerbi/
│ ├── dashboards/
│ └── datasets/
│
├── lovable/
│ ├── insights-diretoria/
│ └── crm-comercial/
│
├── scripts/
│ ├── python/
│ └── utilitarios/
│
└── credentials-doc/
```

---

# 📁 Organização por Camada

## 🗄 SQL

Separado por engine:

- `postgresql/` → Base do DW
- `mysql/` → Consultas operacionais

Subdividido por:
- base-estrutural
- relatorios
- apoio-n8n

---

## 🧱 Pentaho

- Transformações (.ktr)
- Jobs (.kjb)

Responsável pela carga e manutenção do Data Warehouse.

---

## 🤖 N8N

- Export dos workflows em formato JSON
- Versionamento obrigatório de alterações

---

## 📊 Power BI

- Dashboards (.pbix)
- Modelos de dataset
- Estrutura organizada por área

---

## 🌐 Lovable

Aplicações desenvolvidas no Lovable:

- Portal de Insights Diretoria
- CRM Comercial
- Outros projetos internos

---

## 🐍 Scripts

Scripts auxiliares:

- Python
- Automação complementar
- Manutenção técnica

---

# 🔐 Política de Segurança

- ❌ Nunca armazenar tokens ou senhas neste repositório.
- ❌ Nunca versionar arquivos com credenciais embutidas.
- ✔ Documentar apenas a estrutura e instruções de criação.

---

# 🔄 Política de Branch

Branches principais:

- `main` → Produção
- `dev` → Desenvolvimento

Fluxo:

1. Criar branch `feature/descricao`
2. Desenvolver
3. Merge para `dev`
4. Testar
5. Merge para `main`

Push direto na `main` é proibido.

---

# 📝 Padrão de Commit

Formato:


tipo: descrição curta


Tipos:

- feat: nova funcionalidade
- fix: correção
- refactor: melhoria estrutural
- docs: documentação
- chore: ajustes internos

Exemplo:


- feat: adiciona sql base faturamento dw
- fix: corrige duplicidade join pedidos
- docs: adiciona template pentaho


---

# 📌 Padrões Obrigatórios

- Todo SQL deve conter cabeçalho informativo.
- Todo fluxo N8N deve ser exportado antes de alteração.
- Toda transformação Pentaho deve ser versionada.
- Nenhum ativo vai para produção sem estar catalogado no Notion.

---

# 👥 Responsáveis

Setor de Dados & Automação  
Gestão técnica e governança do grupo.

---

# 📎 Observação Final

Este repositório representa a base técnica oficial do setor.  
Qualquer modificação deve seguir os padrões estabelecidos neste documento.
