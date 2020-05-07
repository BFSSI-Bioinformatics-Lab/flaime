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
                sh ''' pip install -r requirements/local.txt '''
            }
        }

        stage('test') {
            agent any
            steps {
                sh '''
                pwd
                ll
                echo hello
                source venv/bin/activate
                pytest
                '''
            }
        }
    }
}
