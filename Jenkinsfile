pipeline {
  agent {
    docker { image 'alpine/git' }
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