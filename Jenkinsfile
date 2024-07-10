pipeline {
    agent any

    environment {
        SCANNER_HOME = tool 'sonar-scanner'
        DOCKERHUB_CREDENTIALS = credentials('5f8b634a-148a-4067-b996-07b4b3276fba')
        BRANCH_NAME = "${GIT_BRANCH.split("/")[1]}"
        SLACK_WEBHOOK = credentials('a3931159-e471-4ec0-8b21-c090749c2c39')
    }

    parameters {
        choice(name: 'DEPLOYMENT', choices: ['DockerContainer', 'Kubernetes'], description: 'Deployment type')
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
                        sh "$SCANNER_HOME/bin/sonar-scanner -Dsonar.projectKey=devops-meeting -Dsonar.projectName=devops-meeting"
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
                sh "trivy fs . > trivy-${env.BRANCH_NAME}-result.txt"
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
                    if (imageTag == 'prod') {
                        sh "sed -i 's/CMD \\[\"python\", \"app.py\"\\]/CMD \\[\"waitress-serve\", \"--listen=*:5000\", \"app:app\"\\]/' Dockerfile"
                        sh "docker build -t idrisniyi94/devops-meeting:${imageTag}-${env.BUILD_ID} ."
                    }
                    else {
                        sh "docker build -t idrisniyi94/devops-meeting:${imageTag}-${env.BUILD_ID} ."
                    }
                }
            }
        }

        stage('Trivy Image Scan') {
            steps {
                script {
                    def imageTag = determineTargetEnvironment()
                    sh "trivy image idrisniyi94/devops-meeting:${imageTag}-${env.BUILD_ID} > devops-meeting-${imageTag}-trivy-result.txt"
                }
            }
        }

        stage('Docker Push') {
            steps {
                script {
                    def imageTag = determineTargetEnvironment()
                    sh "docker push idrisniyi94/devops-meeting:${imageTag}-${env.BUILD_ID}"
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    if params.DEPLOYMENT == 'DockerContainer' {
                        def containerName = "devops-meeting-${env.BRANCH_NAME}"
                    } else {
                        dir('./k8s') {
                            kubeconfig(credentialsId: '3f12ff7b-93cb-4ea5-bc21-79bcf5fb1925', serverUrl: '') {
                                def targetEnvironment = determineTargetEnvironment()
                                sh "kubectl delete -f ${targetEnvironment}-deployment.yaml"
                                sh "sed -i 's/devops-meeting:.*/devops-meeting:${targetEnvironment}-${env.BUILD_ID}/' ${targetEnvironment}-deployment.yaml"
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
        success {
           
            slackSend channel: '#alerts', color: 'good', message: "${currentBuild.currentResult}: \nJOB_NAME: ${env.JOB_NAME} \nBUILD_NUMBER: ${env.BUILD_NUMBER} \nBRANCH_NAME: ${env.BRANCH_NAME}. \n More Info ${env.BUILD_URL}"
        }
        failure {

            slackSend channel: '#alerts', color: 'danger', message: "${currentBuild.currentResult}: \nJOB_NAME: ${env.JOB_NAME} \nBUILD_NUMBER: ${env.BUILD_NUMBER} \nBRANCH_NAME: ${env.BRANCH_NAME}. \n More Info ${env.BUILD_URL}"
        }
    }      
}


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
