pipeline {
    environment {
        // https://jenkins.io/doc/book/using/using-credentials/#configuring-credentials
        SECRET_KEY = credentials('flaim-secret-key')
        FLAIM_DB_USER = credentials('flaim-db-user')
        FLAIM_DB_PASSWORD = credentials('flaim-db-password')
        REDIS_PASSWORD = credentials('flaim-redis-password')
        POSTGRESQL_URL = credentials('flaim-postgresql-url')
        DEBUG = 'on'
    }
    agent none

    stages {
        stage('build') {
            agent {
                docker {
                    image 'python:3.7-slim-buster'
                    args '--user 0:0'  // https://stackoverflow.com/questions/51648534/unable-to-pip-install-in-docker-image-as-agent-through-jenkins-declarative-pipel
                }
                steps {
                    sh '''
                       pip install -r requirements/local.txt
                       '''
                }
            }
            stage('test') {
                agent {
                    docker {
                        image 'postgres:12.2'
                        args '--user 0:0'  // https://stackoverflow.com/questions/51648534/unable-to-pip-install-in-docker-image-as-agent-through-jenkins-declarative-pipel
                    }
                }

                steps {
                    sh '''
                       echo 'test'
                       '''
                }
            }
        }
    }
}
