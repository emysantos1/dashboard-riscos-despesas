"""
Gerador de dataset sintético — Despesas Corporativas com sinais de risco.

Cria um CSV realista (dados 100% fictícios) simulando reembolsos e gastos em
cartão corporativo, com padrões de risco propositalmente embutidos para serem
detectados pela análise. Reprodutível via seed fixa.

Uso:
    python scripts/gerar_dados.py
Saída:
    data/despesas_corporativas.csv
"""

import csv
import os
import random
from datetime import date, datetime, timedelta

random.seed(42)  # reprodutibilidade

# ---------------------------------------------------------------------------
# Parâmetros de negócio
# ---------------------------------------------------------------------------
DATA_INICIO = date(2024, 1, 1)
DATA_FIM = date(2025, 6, 30)
N_TRANSACOES = 2200

DEPARTAMENTOS = [
    "Comercial", "Marketing", "Engenharia", "Produto",
    "Financeiro", "Operações", "RH", "Diretoria",
]

# categoria -> (limite_politica_por_transacao, faixa_valor_normal)
CATEGORIAS = {
    "Viagem - Aéreo":     (3500, (600, 2800)),
    "Hospedagem":         (600,  (180, 550)),
    "Alimentação":        (150,  (25, 140)),
    "Transporte/App":     (120,  (12, 90)),
    "Material Escritório":(400,  (30, 350)),
    "Software/TI":        (2000, (49, 1800)),
    "Marketing/Eventos":  (5000, (300, 4500)),
    "Consultoria":        (8000, (1500, 7500)),
    "Representação":      (500,  (120, 480)),
}

FORNECEDORES = {
    "Viagem - Aéreo":      ["LATAM", "GOL", "Azul", "Decolar", "CVC Corp"],
    "Hospedagem":          ["Rede Accor", "Ibis", "Booking", "Airbnb Corp", "Hotel Transamérica"],
    "Alimentação":         ["iFood", "Restaurante Central", "Padaria Real", "Outback", "Coco Bambu"],
    "Transporte/App":      ["Uber", "99", "Táxi Legal", "Localiza", "Movida"],
    "Material Escritório": ["Kalunga", "Amazon", "Mercado Livre", "Papelaria Uni", "Staples"],
    "Software/TI":         ["Microsoft", "Google Cloud", "AWS", "Adobe", "Zoom", "Atlassian"],
    "Marketing/Eventos":   ["Meta Ads", "Google Ads", "Agência Prisma", "Even Pro", "Gráfica Sol"],
    "Consultoria":         ["Consult XP", "Advisory One", "BR Partners", "TechAdvisors"],
    "Representação":       ["Restaurante Fasano", "Wine Bar", "Club House", "Bistrô 22"],
}

# Fornecedores "atípicos" (não constam na base oficial de fornecedores homologados)
FORNECEDORES_ATIPICOS = ["Fornecedor Novo LTDA", "JM Serviços ME", "Comercial Alfa", "XPTO Solutions"]

COLABORADORES = [
    ("Ana Ribeiro", "Comercial"), ("Bruno Costa", "Comercial"), ("Carla Menezes", "Marketing"),
    ("Diego Alves", "Engenharia"), ("Eduarda Lima", "Engenharia"), ("Felipe Souza", "Produto"),
    ("Gabriela Rocha", "Financeiro"), ("Henrique Dias", "Operações"), ("Isabela Nunes", "RH"),
    ("João Pedro", "Diretoria"), ("Karina Melo", "Comercial"), ("Lucas Fernandes", "Marketing"),
    ("Mariana Teixeira", "Produto"), ("Nathan Oliveira", "Operações"), ("Olívia Cardoso", "Financeiro"),
    ("Paulo Henrique", "Diretoria"), ("Renata Barros", "Engenharia"), ("Sérgio Ramos", "Comercial"),
]

APROVADORES = ["Gestor A", "Gestor B", "Gestor C", "Gestor D", "Diretoria"]
FORMAS_PGTO = ["Cartão Corporativo", "Reembolso", "Boleto"]

# Feriados nacionais (subconjunto) para sinalizar gasto em feriado
FERIADOS = {
    date(2024, 1, 1), date(2024, 2, 12), date(2024, 2, 13), date(2024, 3, 29),
    date(2024, 4, 21), date(2024, 5, 1), date(2024, 9, 7), date(2024, 10, 12),
    date(2024, 11, 2), date(2024, 11, 15), date(2024, 12, 25),
    date(2025, 1, 1), date(2025, 3, 3), date(2025, 3, 4), date(2025, 4, 18),
    date(2025, 4, 21), date(2025, 5, 1), date(2025, 6, 19),
}


def data_aleatoria():
    delta = (DATA_FIM - DATA_INICIO).days
    return DATA_INICIO + timedelta(days=random.randint(0, delta))


def valor_normal(faixa):
    lo, hi = faixa
    return round(random.uniform(lo, hi), 2)


def hora_comercial():
    return f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}"


def hora_madrugada():
    return f"{random.randint(0, 5):02d}:{random.randint(0, 59):02d}"


linhas = []
tid = 1000


def add(data_despesa, colaborador, depto, categoria, fornecedor, valor,
        forma, aprovador, comprovante, data_sub, hora_sub, descricao):
    global tid
    tid += 1
    limite = CATEGORIAS[categoria][0]
    linhas.append({
        "id_transacao": f"TX{tid}",
        "data_despesa": data_despesa.isoformat(),
        "colaborador": colaborador,
        "departamento": depto,
        "categoria": categoria,
        "fornecedor": fornecedor,
        "descricao": descricao,
        "valor": f"{valor:.2f}",
        "moeda": "BRL",
        "forma_pagamento": forma,
        "limite_politica": f"{limite:.2f}",
        "aprovador": aprovador,
        "status_aprovacao": random.choices(
            ["Aprovado", "Pendente", "Rejeitado"], weights=[0.86, 0.10, 0.04])[0],
        "possui_comprovante": comprovante,
        "data_submissao": data_sub.isoformat(),
        "hora_submissao": hora_sub,
    })


# ---------------------------------------------------------------------------
# 1) Transações "normais" (maioria)
# ---------------------------------------------------------------------------
n_normais = int(N_TRANSACOES * 0.80)
for _ in range(n_normais):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(list(CATEGORIAS.keys()))
    fornecedor = random.choice(FORNECEDORES[categoria])
    valor = valor_normal(CATEGORIAS[categoria][1])
    dt = data_aleatoria()
    # despesa em dia útil na maior parte dos casos normais
    while dt.weekday() >= 5 and random.random() < 0.7:
        dt = data_aleatoria()
    data_sub = dt + timedelta(days=random.randint(0, 7))
    add(dt, colaborador, depto, categoria, fornecedor, valor,
        random.choice(FORMAS_PGTO), random.choice(APROVADORES), "Sim",
        data_sub, hora_comercial(), f"Despesa de {categoria.lower()}")

# ---------------------------------------------------------------------------
# 2) RISCO: acima do limite da política
# ---------------------------------------------------------------------------
for _ in range(70):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(list(CATEGORIAS.keys()))
    limite = CATEGORIAS[categoria][0]
    valor = round(limite * random.uniform(1.15, 2.2), 2)
    dt = data_aleatoria()
    add(dt, colaborador, depto, categoria, random.choice(FORNECEDORES[categoria]),
        valor, random.choice(FORMAS_PGTO), random.choice(APROVADORES), "Sim",
        dt + timedelta(days=random.randint(0, 5)), hora_comercial(),
        f"{categoria} acima do padrão")

# ---------------------------------------------------------------------------
# 3) RISCO: valores redondos altos (ex.: 1000.00, 2500.00)
# ---------------------------------------------------------------------------
for _ in range(45):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(["Consultoria", "Marketing/Eventos", "Software/TI"])
    valor = float(random.choice([1000, 1500, 2000, 2500, 3000, 5000]))
    dt = data_aleatoria()
    add(dt, colaborador, depto, categoria, random.choice(FORNECEDORES[categoria]),
        valor, random.choice(FORMAS_PGTO), random.choice(APROVADORES), "Sim",
        dt + timedelta(days=random.randint(0, 6)), hora_comercial(),
        f"{categoria} - valor fechado")

# ---------------------------------------------------------------------------
# 4) RISCO: despesa em fim de semana / feriado
# ---------------------------------------------------------------------------
for _ in range(60):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(["Alimentação", "Transporte/App", "Representação", "Hospedagem"])
    dt = data_aleatoria()
    # força fim de semana ou feriado
    if random.random() < 0.5:
        while dt.weekday() < 5:
            dt = data_aleatoria()
    else:
        dt = random.choice(list(FERIADOS))
    valor = valor_normal(CATEGORIAS[categoria][1])
    add(dt, colaborador, depto, categoria, random.choice(FORNECEDORES[categoria]),
        valor, random.choice(FORMAS_PGTO), random.choice(APROVADORES), "Sim",
        dt + timedelta(days=random.randint(0, 4)), hora_comercial(),
        f"{categoria} em dia não útil")

# ---------------------------------------------------------------------------
# 5) RISCO: duplicidade (mesmo colaborador, fornecedor, valor, ~mesma data)
# ---------------------------------------------------------------------------
for _ in range(25):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(list(CATEGORIAS.keys()))
    fornecedor = random.choice(FORNECEDORES[categoria])
    valor = valor_normal(CATEGORIAS[categoria][1])
    dt = data_aleatoria()
    for k in range(2):  # par duplicado
        add(dt + timedelta(days=k), colaborador, depto, categoria, fornecedor, valor,
            "Reembolso", random.choice(APROVADORES), "Sim",
            dt + timedelta(days=k + 1), hora_comercial(), f"{categoria} (possível duplicidade)")

# ---------------------------------------------------------------------------
# 6) RISCO: fracionamento (várias despesas logo abaixo do limite de aprovação)
#    Limite de alçada de aprovação simples assumido = R$ 500
# ---------------------------------------------------------------------------
LIMITE_ALCADA = 500
for _ in range(20):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(["Material Escritório", "Software/TI", "Representação"])
    dt = data_aleatoria()
    for k in range(random.randint(3, 4)):
        valor = round(random.uniform(LIMITE_ALCADA - 60, LIMITE_ALCADA - 5), 2)
        add(dt, colaborador, depto, categoria, random.choice(FORNECEDORES[categoria]),
            valor, "Cartão Corporativo", random.choice(APROVADORES), "Sim",
            dt + timedelta(days=1), hora_comercial(),
            f"{categoria} (compra fracionada no mesmo dia)")

# ---------------------------------------------------------------------------
# 7) RISCO: sem comprovante em valor alto
# ---------------------------------------------------------------------------
for _ in range(40):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(["Consultoria", "Marketing/Eventos", "Viagem - Aéreo", "Software/TI"])
    valor = round(random.uniform(800, 4000), 2)
    dt = data_aleatoria()
    add(dt, colaborador, depto, categoria, random.choice(FORNECEDORES[categoria]),
        valor, random.choice(FORMAS_PGTO), random.choice(APROVADORES), "Não",
        dt + timedelta(days=random.randint(0, 5)), hora_comercial(),
        f"{categoria} sem comprovante anexado")

# ---------------------------------------------------------------------------
# 8) RISCO: fornecedor atípico (não homologado)
# ---------------------------------------------------------------------------
for _ in range(30):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(["Consultoria", "Software/TI", "Marketing/Eventos", "Material Escritório"])
    valor = round(random.uniform(400, 6000), 2)
    dt = data_aleatoria()
    add(dt, colaborador, depto, categoria, random.choice(FORNECEDORES_ATIPICOS),
        valor, random.choice(FORMAS_PGTO), random.choice(APROVADORES), "Sim",
        dt + timedelta(days=random.randint(0, 6)), hora_comercial(),
        f"{categoria} - fornecedor não homologado")

# ---------------------------------------------------------------------------
# 9) RISCO: submissão em horário atípico (madrugada)
# ---------------------------------------------------------------------------
for _ in range(25):
    colaborador, depto = random.choice(COLABORADORES)
    categoria = random.choice(list(CATEGORIAS.keys()))
    valor = valor_normal(CATEGORIAS[categoria][1])
    dt = data_aleatoria()
    add(dt, colaborador, depto, categoria, random.choice(FORNECEDORES[categoria]),
        valor, random.choice(FORMAS_PGTO), random.choice(APROVADORES), "Sim",
        dt + timedelta(days=random.randint(0, 3)), hora_madrugada(),
        f"{categoria} submetida fora do horário")

# ---------------------------------------------------------------------------
# Injeção de "sujeira" realista — será tratada na etapa de LIMPEZA (01_limpeza.py).
# Simula os problemas típicos de uma base exportada de um sistema real.
# ---------------------------------------------------------------------------
import copy

# a) espaços extras em textos (erro comum de digitação/importação)
for r in random.sample(linhas, 40):
    r["colaborador"] = "  " + r["colaborador"] + " "
    r["fornecedor"] = r["fornecedor"] + "  "

# b) capitalização inconsistente em forma_pagamento
for r in random.sample(linhas, 60):
    r["forma_pagamento"] = random.choice([r["forma_pagamento"].upper(),
                                          r["forma_pagamento"].lower()])

# c) linhas 100% duplicadas (erro de importação — a mesma linha lançada 2x)
for r in random.sample(linhas, 15):
    linhas.append(copy.deepcopy(r))

# d) valores inválidos (<= 0) por erro de digitação
for r in random.sample(linhas, 8):
    r["valor"] = "0.00"

# ---------------------------------------------------------------------------
# Embaralhar e salvar
# ---------------------------------------------------------------------------
random.shuffle(linhas)

os.makedirs("data", exist_ok=True)
campos = [
    "id_transacao", "data_despesa", "colaborador", "departamento", "categoria",
    "fornecedor", "descricao", "valor", "moeda", "forma_pagamento",
    "limite_politica", "aprovador", "status_aprovacao", "possui_comprovante",
    "data_submissao", "hora_submissao",
]
with open("data/despesas_corporativas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(linhas)

print(f"OK - {len(linhas)} transações geradas em data/despesas_corporativas.csv")
