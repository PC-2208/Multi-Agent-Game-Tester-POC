pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        IMAGE      = 'game-tester'
        DEPLOY_DIR = '/opt/game-tester'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t $IMAGE:$BUILD_NUMBER -t $IMAGE:latest .'
            }
        }

        stage('Smoke test') {
            steps {
                // Imports aur folder structure sahi hai ya nahi, ye yahin pakad lega
                sh 'docker run --rm $IMAGE:$BUILD_NUMBER python -c "import main; print(\'import ok\')"'
            }
        }

        stage('Deploy') {
            steps {
                sh 'cd $DEPLOY_DIR && docker compose up -d --no-deps game-tester'
            }
        }

        stage('Health check') {
            steps {
                sh '''
                for i in $(seq 1 20); do
                  if curl -fsS http://127.0.0.1:8001/reports > /dev/null; then
                    echo "App healthy"; exit 0
                  fi
                  sleep 3
                done
                docker logs --tail 100 game-tester
                exit 1
                '''
            }
        }
    }

    post {
        success { echo 'Deployed' }
        failure { echo 'Deploy failed. Console Output check karo.' }
        always  { cleanWs() }
    }
}