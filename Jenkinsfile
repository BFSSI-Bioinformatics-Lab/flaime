
pipeline {
  agent { docker { image 'python:3.7-slim-buster' } }
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
