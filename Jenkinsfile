pipeline {
  agent {
    docker { dockerfile true }
  }
  stages {
    stage('Checkout') {
        steps {
            checkout(scm)
        }
    }

    stage('Merge') {
        steps {
            sh "git pull"
            sh "git checkout master"
        }
    }


  }
}