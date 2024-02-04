pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('d4506f04-b98c-47db-95ce-018ceac27ba6')
        BRANCH_NAME = "${GIT_BRANCH.split("/")[1]}"
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
                withSonarQubeEnv('sonar-server') {
                    sh "$SCANNER_HOME/bin/sonar-scanner -Dsonar.projectKey=devops-meeting -Dsonar.projectName=devops-meeting -Dsonar.sources=. -Dsonar.host.url=http://192.168.0.43:9000 -Dsonar.login=sqp_8a0e7752fe6052769eeeb3942f42d125de0c4855"
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
                def imageTag = determineTargetEnvironment()
                sh "trivy image idrisniyi94/devops-meeting:${imageTag} > image-scan.txt"
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
                            sh "kubectl apply -f ${targetEnvironment}-deployment.yaml"
                            sh "kubectl apply -f ${targetEnvironment}-service.yaml"
                        }
                    }
                }
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