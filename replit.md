# Overview

GLPI Dashboard is a comprehensive business intelligence system for monitoring and analyzing IT service management (ITSM) data from GLPI (Gestionnaire Libre de Parc Informatique). The project provides a React-based frontend dashboard with a Flask backend API that integrates with GLPI's REST API to deliver real-time metrics, technician performance rankings, and operational insights.

The system focuses on tracking ticket metrics across different service levels (N1-N4), technician performance analysis, and providing detailed monitoring capabilities for IT support operations.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture (Migração Completa - 13/09/2025)
- **React 18** com TypeScript para type safety
- **Vite** como build tool e servidor de desenvolvimento
- **TailwindCSS** com shadcn/ui components para design moderno
- **Design do Figma** implementado com cor primária #5A9BD4
- **Integração completa** com dados reais do GLPI via API
- **Auto-refresh** a cada 30 segundos para dados em tempo real

## Backend Architecture
- **Flask** web framework with Blueprint-based route organization
- **Clean Architecture** principles with progressive refactoring pattern
- **Pydantic** for data validation and serialization
- **Redis** for caching and session management
- **Structured logging** with JSON format for observability
- **Prometheus metrics** integration for monitoring

## Data Flow Pattern
The system implements a multi-layered data flow:
1. Frontend requests data through API service layer
2. Flask routes handle HTTP requests with validation
3. GLPI service layer manages authentication and API calls
4. Response formatting and caching layers optimize performance
5. Structured logging tracks all operations with correlation IDs

## Authentication & Security
- GLPI API token-based authentication (App Token + User Token)
- Session management with automatic token refresh
- CORS configuration for cross-origin requests
- Input validation and sanitization at multiple layers

## Performance Optimization
- **Multi-level caching**: Redis backend cache + React Query frontend cache
- **Request debouncing** and throttling for API calls
- **Connection pooling** for database connections
- **Lazy loading** for components and data
- **Response compression** and optimization

## Service Level Mapping
The system maps GLPI data to service levels:
- **N1**: Basic support (Group ID 89)
- **N2**: Intermediate support (Group ID 90) 
- **N3**: Advanced support (Group ID 91)
- **N4**: Expert support (Group ID 92)

## Observability & Monitoring
- **Structured logging** with correlation IDs for request tracing
- **Prometheus metrics** collection for performance monitoring
- **Health check endpoints** for system status
- **Automated alerting** system for data inconsistencies
- **Progressive refactoring** monitoring for architecture migration

# External Dependencies

## Core Infrastructure
- **GLPI API**: Primary data source at `http://10.73.0.79/glpi/apirest.php`
- **Redis**: Caching layer and session storage
- **Prometheus**: Metrics collection and monitoring (optional)

## GLPI Integration
- **API Authentication**: Requires GLPI_APP_TOKEN and GLPI_USER_TOKEN
- **REST API Endpoints**: Uses GLPI's search API for tickets, users, and groups
- **Session Management**: Maintains authenticated sessions with automatic refresh
- **Field Discovery**: Automatically discovers GLPI schema field mappings

## Development Tools
- **Node.js ecosystem**: React, Vite, TypeScript toolchain
- **Python ecosystem**: Flask, Pydantic, Redis client libraries  
- **Testing frameworks**: Vitest (frontend), pytest (backend), Playwright (E2E)
- **Code quality**: ESLint, Prettier, Black, isort for formatting

## Monitoring & Alerting
- **ELK Stack** compatibility for log aggregation (optional)
- **Grafana Loki** integration for log visualization (optional)
- **Email/Slack notifications** for critical alerts (configurable)
- **Automated reporting** system for data consistency monitoring

## Optional Extensions
- **PostgreSQL**: Database support for extended analytics
- **Docker**: Containerization support
- **CI/CD pipelines**: GitHub Actions integration
- **Performance profiling**: py-spy and memory-profiler tools