# Arquitetura Android - Urgências Hospitalares

## Visão Geral
Esta aplicação foi construída seguindo os princípios de **Clean Architecture** e o padrão **MVVM**, garantindo que o Administrador tenha acesso universal e insights de IA em tempo real.

## Stack Tecnológica
- **Linguagem:** Kotlin 2.0+
- **UI:** Jetpack Compose (Material 3)
- **Injeção de Dependência:** Hilt (Dagger)
- **Rede:** Retrofit + OkHttp (Ligação ao FastAPI)
- **Base de Dados Local:** Room (Offline-First)
- **Real-time & Push:** Firebase (FCM)
- **Gráficos:** Vico Charts (para Analytics de IA)

## Estrutura de Pastas (Módulos)
- `di/`: Módulos de Injeção de Dependência (Network, Database, Repository).
- `domain/`: Regras de negócio puras (Models, Repository Interfaces, UseCases).
- `data/`: Implementação de dados (Remote API, Room DAO, Repositories).
- `ui/`: Camada de apresentação (ViewModels, Composable Screens, Theme).

## Fluxo de IA & Analytics
O Android consome os dados do script `analytics_afluencia.py` através de endpoints REST e apresenta dashboards preditivos ao Administrador, permitindo ações preventivas na gestão hospitalar.
