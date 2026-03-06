# CredCode - Terminal Financeiro 🚀

O **CredCode** é um sistema de gestão financeira (Terminal Financeiro) desenvolvido com uma arquitetura baseada em microsserviços, separando o backend (Django) do frontend (Vue.js). Este repositório foca-se nas práticas de DevOps, implementando contentorização e pipelines de CI/CD para automação de builds.

## 🛠️ Stack Tecnológica

* **Backend:** Python 3.11, Django 4.2+, Django REST Framework, SimpleJWT.
* **Frontend:** Vue.js 3, Vite, Pinia, Vue Router.
* **Base de Dados:** SQLite (ambiente de desenvolvimento).
* **DevOps:** Docker, Docker Compose, GitHub Actions, GitHub Container Registry (GHCR).

---

## ⚙️ Arquitetura DevOps e Infraestrutura

### Contentorização (Docker)
O backend da aplicação está totalmente contentorizado para garantir consistência entre os ambientes de desenvolvimento, teste e produção.

* **Dockerfile:** Utiliza a imagem oficial `python:3.11-slim` para otimizar o tamanho final da imagem. Define variáveis de ambiente essenciais (`PYTHONDONTWRITEBYTECODE` e `PYTHONUNBUFFERED`) para garantir que os logs são enviados corretamente para a saída padrão e que não são gerados ficheiros `.pyc` desnecessários.
* **Docker Compose:** O ficheiro `docker-compose.yml` orquestra o serviço `web` (backend). Ele mapeia o diretório local para dentro do contentor (volume `./backend:/app`), permitindo _hot-reload_ durante o desenvolvimento, e expõe a porta `8000`.

### Pipeline CI/CD (GitHub Actions)
O projeto possui um fluxo de Integração Contínua (CI) configurado em `.github/workflows/ci.yaml`.

**Gatilho (Trigger):** A pipeline é ativada automaticamente a cada `push` para os branches `main` ou `master`.

**Etapas do Job (`build-and-push-image`):**
1.  **Checkout:** Clona o código-fonte do repositório.
2.  **Preparação de Variáveis:** Executa um script Bash (`IMAGE_NAME_LOWER=${GITHUB_REPOSITORY,,}`) para converter o nome do repositório para minúsculas. Este é um truque importante de DevOps, pois os registries Docker não aceitam letras maiúsculas em nomes de imagens.
3.  **Login no Registry:** Autentica-se no GitHub Container Registry (`ghcr.io`) utilizando o token de segurança fornecido nativamente pelo GitHub (`secrets.GITHUB_TOKEN`).
4.  **Extração de Metadados:** Gera tags automáticas para a imagem Docker (ex: `latest` para a _default branch_ e tags curtas de SHA baseadas no commit).
5.  **Build e Push:** Utiliza o diretório `./backend` como contexto de build, constrói a imagem Docker e faz o push automático para o `ghcr.io`.

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
* Docker e Docker Compose instalados.
* Node.js (versão 20+ recomendada) e npm instalados.

### 1. Iniciar o Backend (via Docker)
Navegue até à raiz do projeto e utilize o Docker Compose para levantar o serviço backend:

```bash
# Constrói a imagem e levanta o contentor em modo detached
docker-compose up -d --build

# Para aplicar as migrações da base de dados no contentor em execução
docker-compose exec web python manage.py migrate

# Para criar um superutilizador (opcional)
docker-compose exec web python manage.py createsuperuser