pipeline {
    environment {
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
                    args '--user 0:0'
                }
            }
            steps {
                sh '''
                 python3 -m venv ./venv
                 source ./venv/bin/activate
                 pip install -r requirements/local.txt
                  '''
            }
        }

        stage('database') {
            agent {
                docker {
                    image 'postgres:12.2'
                    args '--user 0:0 -p 5432:5432 -v /var/run/postgresql:/var/run/postgresql -d'
                }
            }
            steps {
                sh '''
                psql -d flaim
                '''
            }
        }

        stage('test') {
            agent {
                docker {
                    image 'python:3.7-slim-buster'
                    args '--user 0:0'
                }
            }
            steps {
                sh '''
                source ./venv/bin/activate
                pytest
                '''
            }
        }
    }
}
