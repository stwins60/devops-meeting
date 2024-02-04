pipeline {
    agent any

    environment {
        SCANNER_HOME = tool 'sonar-scanner'
        DOCKERHUB_CREDENTIALS = credentials('d4506f04-b98c-47db-95ce-018ceac27ba6')
        BRANCH_NAME = "${GIT_BRANCH.split("/")[1]}"
        SLACK_WEBHOOK = 'https://hooks.slack.com/services/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'
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }
        stage('Git Checkout') {
            steps {
                checkout scmGit(branches: [[name: '*/dev'], [name: '*/qa'], [name: '*/prod']], extensions: [], userRemoteConfigs: [[url: 'https://github.com/stwins60/devops-meeting.git']])
            }
        }

        stage('Sonarqube Analysis') {
            steps {
                script {
                    withSonarQubeEnv('sonar-server') {
                        sh "$SCANNER_HOME/bin/sonar-scanner -Dsonar.projectKey=devops-meeting -Dsonar.projectName=devops-meeting -Dsonar.sources=. -Dsonar.host.url=http://192.168.0.43:9000 -Dsonar.login=sqp_8a0e7752fe6052769eeeb3942f42d125de0c4855"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    withSonarQubeEnv('sonar-server') {
                        waitForQualityGate abortPipeline: false, credentialsId: 'sonar-token'
                    }
                }
            }
        }

        stage('Trivy File Scan') {
            steps {
                sh "trivy fs . > trivy-result.txt"
            }
        }

        stage("Docker Login") {
            steps {
                sh "echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin"
                echo "Login Succeeded"
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    def imageTag = determineTargetEnvironment()
                    sh "docker build -t idrisniyi94/devops-meeting:${imageTag} ."
                }
            }
        }

        stage('Trivy Image Scan') {
            steps {
                script {
                    def imageTag = determineTargetEnvironment()
                    sh "trivy image idrisniyi94/devops-meeting:${imageTag} > devops-meeting-image-scan.txt"
                }
            }
        }

        stage('Docker Push') {
            steps {
                script {
                    def imageTag = determineTargetEnvironment()
                    sh "docker push idrisniyi94/devops-meeting:${imageTag}"
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    dir('./k8s') {
                        kubeconfig(credentialsId: '500a0599-809f-4de0-a060-0fdbb6583332', serverUrl: '') {
                            def targetEnvironment = determineTargetEnvironment()
                            sh "kubectl delete -f ${targetEnvironment}-deployment.yaml"
                            sh "kubectl apply -f ${targetEnvironment}-deployment.yaml"
                            sh "kubectl apply -f ${targetEnvironment}-service.yaml"
                        }
                    }
                }
            }
        }
    }
}
post {
    always {
        script {
            message = """
            Build ${currentBuild.result}: \n
            Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}) \n
            Branch ${env.BRANCH_NAME} \n
            """
            if (env.BRANCH_NAME == 'dev') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"${message}\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'qa') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"${message}\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'prod') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"${message}\"}' ${SLACK_WEBHOOK}"
            }
        }
    }
    success {
        script {
            if (env.BRANCH_NAME == 'dev') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was successful\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'qa') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was successful\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'prod') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was successful\"}' ${SLACK_WEBHOOK}"
            }
        }
    }
    failure {
        script {
            if (env.BRANCH_NAME == 'dev') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} failed\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'qa') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} failed\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'prod') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} failed\"}' ${SLACK_WEBHOOK}"
            }
        
        }
    }
    unstable {
        script {
            if (env.BRANCH_NAME == 'dev') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was unstable\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'qa') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was unstable\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'prod') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was unstable\"}' ${SLACK_WEBHOOK}"
            }
        }
    }
    changed {
        script {
            if (env.BRANCH_NAME == 'dev') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was changed\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'qa') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was changed\"}' ${SLACK_WEBHOOK}"
            }
            else if (env.BRANCH_NAME == 'prod') {
                sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${env.BRANCH_NAME} was changed\"}' ${SLACK_WEBHOOK}"
            }
        }
    }
}

// def gitCheckout(branch, repositoryUrl) {
//     git branch: branch, url: repositoryUrl
// }

def determineTargetEnvironment() {
    def branchName = env.BRANCH_NAME
    if (branchName == 'qa') {
        return 'qa'
    } else if (branchName == 'prod') {
        return 'prod'
    } else {
        return 'dev'
    }
}

def COLOR_MAP = [
    'dev': 'blue',
    'qa': 'yellow',
    'prod': 'red',
    'success': 'green',
    'failure': 'red'
]