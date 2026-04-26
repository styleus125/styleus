pipeline {
    agent any

    environment {
        IMAGE_NAME    = "YOUR_DOCKERHUB_USERNAME/dlo-web"
        IMAGE_TAG     = "${IMAGE_NAME}:${BUILD_NUMBER}"
        IMAGE_LATEST  = "${IMAGE_NAME}:latest"
        VPS_USER      = "root"
        VPS_HOST      = "YOUR_VPS_IP"
        DEPLOY_DIR    = "/opt/dlo"
        COMPOSE_FILE  = "docker-compose.yml"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    pip install flake8 --quiet
                    flake8 . --max-line-length=120 --exclude=__pycache__,.git,venv
                '''
            }
        }

        stage('Build Image') {
            steps {
                sh "docker build -t ${IMAGE_TAG} -t ${IMAGE_LATEST} ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ''' + IMAGE_TAG + '''
                        docker push ''' + IMAGE_LATEST + '''
                    '''
                }
            }
        }

        stage('Deploy to VPS') {
            steps {
                sshagent(credentials: ['vps-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} '
                            cd ${DEPLOY_DIR} &&
                            git pull origin main &&
                            docker compose -f ${COMPOSE_FILE} pull &&
                            docker compose -f ${COMPOSE_FILE} up -d --remove-orphans &&
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
            echo "Pipeline failed at stage: ${STAGE_NAME}. Check logs above."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
