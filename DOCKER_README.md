# BakeryAI API Docker Deployment

This document provides instructions on how to build and run the BakeryAI API using Docker and Docker Compose.

## Prerequisites

- Docker
- Docker Compose

## Running the Application

1.  **Navigate to the `deployment` directory:**

    ```bash
    cd deployment
    ```

2.  **Create a `.env` file in the project root:**

    Create a `.env` file in the root directory of the project (the one containing the `deployment` and `notebooks` folders) and add your API keys and project name:

    ```
    OPENAI_API_KEY="your-openai-api-key"
    LANGSMITH_API_KEY="your-langsmith-api-key"
    LANGSMITH_PROJECT="your-langsmith-project-name"
    ```

3.  **Build and run the Docker container:**

    From the `deployment` directory, run the following command. This command explicitly tells Docker Compose where to find your `.env` file:

    ```bash
    docker-compose --env-file ../.env up --build
    ```

    This command will build the Docker image and start the BakeryAI API service. The API will be available at `http://localhost:8000`.

### Alternative: Separating Build and Run Steps

If you prefer to build the image and run the container in separate steps, you can use the following commands from the `deployment` directory.

1.  **Build the image:**
    ```bash
    docker-compose --env-file ../.env build
    ```

2.  **Run the container:**
    ```bash
    docker-compose --env-file ../.env up
    ```

    To run the container in the background (detached mode), use the `-d` flag:
    ```bash
    docker-compose --env-file ../.env up -d
    ```

## Interacting with the API

You can interact with the API using the `notebooks/Session4_Notebook2_LangServe_Deployment_v2.ipynb` notebook, or by sending requests directly to the API endpoints.

The API documentation is available at `http://localhost:8000/docs`.
