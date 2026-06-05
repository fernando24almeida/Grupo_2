# Documentação de Fluxo de Dados (DFD) - Sistema de Gestão Clínica

Este documento descreve a arquitetura de dados e o fluxo de informação do Sistema de Gestão Clínica, abrangendo desde o nível macro (contexto) até ao detalhe dos processos internos.

---

## 1. Diagrama de Contexto (Nível 0)
O objetivo deste diagrama é mostrar os limites do sistema e as suas interações com as entidades externas.

```mermaid
graph LR
    %% Entidades Externas
    U[Utente / Paciente]
    S[Staff Médico/Admin]
    E[Serviço de Email]

    %% Sistema Central
    subgraph Sistema_Gestao_Clinica [Sistema de Gestão Clínica]
        P[API Backend & Base de Dados]
    end

    %% Fluxos de Dados
    U -- Pedido de Acesso/Dados Clínicos --> P
    P -- Notificações/Dados de Saúde --> U
    
    S -- Gestão de Episódios/Triagem --> P
    P -- Dashboards e Alertas AI --> S
    
    P -- Códigos de Verificação/MFA --> E
    E -- Envio de Email --> U
    E -- Envio de Email --> S
```

---

## 2. Diagrama de Fluxo de Dados (Nível 1)
Detalhamento dos grandes módulos do sistema, repositórios de dados e as interconexões principais.

```mermaid
flowchart TD
    %% Entidades Externas
    U([Utente - Mobile])
    S([Staff - Web])
    E([Serviço de Email])

    %% Processos
    P1{1.0 Autenticação e MFA}
    P2{2.0 Gestão Clínica}
    P3{3.0 Analytics e AI}
    P4{4.0 Auditoria e Segurança}

    %% Depósitos de Dados (Data Stores)
    D1[(DB: Utilizadores)]
    D2[(DB: Registos Clínicos)]
    D3[(DB: Logs Auditoria)]

    %% Fluxos de Dados
    U --> P1
    S --> P1
    P1 --- D1
    P1 --> E

    S --> P2
    P2 --- D2
    P2 --> U

    D2 --> P3
    P3 --> S
    P3 --- D2

    P1 --> P4
    P2 --> P4
    P4 --- D3
```

---

## 3. Detalhes de Nível 2 (Processos Específicos)

### 3.1. Autenticação e MFA (Processo 1.0)
Focado na segurança de acesso e recuperação de conta.

```mermaid
flowchart TD
    U([Utilizador])
    E([Provedor de Email])

    P1_1{1.1 Validação Credenciais}
    P1_2{1.2 Verificação MFA}
    P1_3{1.3 Geração Token JWT}

    D1[(DB: Utilizadores)]
    D3[(DB: Secrets/Tokens)]

    U --> P1_1
    P1_1 --- D1
    P1_1 --> P1_2
    U --> P1_2
    P1_2 --- D3
    P1_2 --> P1_3
    P1_3 --> U
```

### 3.2. Triagem de Manchester (Processo 2.0)
Fluxo clínico de atribuição de prioridade.

```mermaid
flowchart TD
    S([Enfermeiro])
    
    P2_1{2.1 Recolha Sinais Vitais}
    P2_2{2.2 Lógica Manchester}
    P2_3{2.3 Atribuição de Fila}

    D2[(DB: Episódios)]
    D3[(DB: Triagens)]

    S --> P2_1
    P2_1 --- D2
    P2_1 --> P2_2
    P2_2 --- D3
    P2_2 --> P2_3
    P2_3 --> S
```

### 3.3. Analytics e AI (Processo 3.0)
Utilização de Machine Learning (Random Forest) para análise de afluência.

```mermaid
flowchart TD
    AD([Administrador])
    P3_1{3.1 Extração e Preparação}
    P3_2{3.2 Treino do Modelo AI}
    P3_3{3.3 Geração Previsões}

    D_HIST[(DB: Histórico)]

    D_HIST --> P3_1
    P3_1 --> P3_2
    P3_2 --> P3_3
    P3_3 --> AD
```

---

## 4. Diagramas de Sequência (Interações Temporais)

### 4.1. Fluxo de Triagem
```mermaid
sequenceDiagram
    participant E as Enfermeiro
    participant API as API Backend
    participant DB as Base de Dados

    E->>API: POST /triagens/manchester
    API->>DB: Verificar Episódio
    API->>API: Calcular Prioridade (Cor)
    API->>DB: INSERT Triagem
    API-->>E: 201 Created + Cor Atribuída
```

### 4.2. Fluxo de Previsão AI
```mermaid
sequenceDiagram
    participant A as Admin
    participant API as API Analytics
    participant AI as Motor Random Forest
    participant DB as Base de Dados

    A->>API: GET /analytics/afluencia
    API->>AI: executar_analytics()
    AI->>DB: SELECT data_h_entr
    DB-->>AI: Registos Históricos
    AI->>AI: Treino e Previsão
    AI-->>API: Métricas e JSON
    API-->>A: Visualização Gráfica
```

---
*Documento gerado automaticamente para o Grupo 2 - Projeto de Gestão Clínica.*
