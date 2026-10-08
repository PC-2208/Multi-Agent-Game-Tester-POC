pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        IMAGE = 'game-tester'
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
                sh 'docker run --rm $IMAGE:$BUILD_NUMBER python -c "import main; print(\'import ok\')"'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker compose up -d --no-deps game-tester'
            }
        }

        stage('Health check') {
            steps {
                sh '''
                for i in $(seq 1 30); do
                  STATUS=$(docker inspect --format '{{.State.Health.Status}}' game-tester 2>/dev/null || echo none)
                  echo "Health: $STATUS"
                  if [ "$STATUS" = "healthy" ]; then exit 0; fi
                  sleep 3
                done
                docker logs --tail 100 game-tester
                exit 1
                '''
            }
        }
    }

    post {
        success { echo 'Deployed: http://localhost:8001' }
        failure { echo 'Deploy failed. check Console Output' }
        always  { cleanWs() }
    }
}