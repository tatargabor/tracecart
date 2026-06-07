pipeline {
    agent any

    triggers {
        githubPush()
    }

    tools {
        nodejs 'node22'
    }

    stages {
        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }

        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }

        stage('Test') {
            steps {
                sh 'npm test'
            }
        }

        stage('Publish') {
            when {
                buildingTag()
                tag pattern: 'v\\d+\\.\\d+\\.\\d+', comparator: 'REGEXP'
            }
            steps {
                withCredentials([string(credentialsId: 'NPM_TOKEN', variable: 'NODE_AUTH_TOKEN')]) {
                    sh '''
                        echo "//registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}" > .npmrc
                        npm publish --access public
                        rm -f .npmrc
                    '''
                }
            }
        }
    }

    post {
        success {
            script {
                if (env.TAG_NAME) {
                    echo "Published @tracecart/cli@${env.TAG_NAME} to npm"
                }
            }
        }
        cleanup {
            sh 'rm -f .npmrc'
        }
    }
}
