pipeline {
    agent any

    environment {
        VPS_USER     = "root"
        VPS_HOST     = "YOUR_VPS_IP"
        DEPLOY_DIR   = "/opt/dlo"
        COMPOSE_FILE = "docker-compose.yml"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint & Deploy to VPS') {
            steps {
                sshagent(credentials: ['vps-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} '
                            cd ${DEPLOY_DIR} &&
                            git pull origin main &&
                            docker run --rm -v \$(pwd):/app -w /app python:3.11-slim sh -c "pip install flake8 --quiet && flake8 . --max-line-length=120 --exclude=__pycache__,.git,venv" &&
                            docker compose -f ${COMPOSE_FILE} up -d --build --remove-orphans &&
                            docker image prune -f
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Deployment successful — build #${BUILD_NUMBER} is live."
        }
        failure {
            echo "Pipeline failed. Check logs above."
        }
    }
}
