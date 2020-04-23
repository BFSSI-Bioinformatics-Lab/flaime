
pipeline {
  agent {
    docker {
        image 'python:3.7-slim-buster'
        args '--user 0:0'
    }
  }
  stages {
    stage('build') {
      steps {
        sh 'pip install -r requirements/local.txt'
      }
    }
    stage('test') {
      steps {
        sh 'pytest'
      }
    }
  }
}
