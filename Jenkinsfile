// CI/CD pipeline for the CMR621 network monitoring system.
//
// Runs on the remote-docker agent, which is the monitoring VM itself. The
// repository is public, so the checkout needs no credentials.
//
// Deployment policy:
//   * only the main branch is deployed to production;
//   * other branches are validated and built but never deployed;
//   * secrets are never read into the workspace or logged; the container reads
//     them from the server directory listed in SECRETS_DIR;
//   * a failed smoke test restores the previously running image.

pipeline {
  agent { label 'remote-docker' }

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 30, unit: 'MINUTES')
  }

  environment {
    COMPOSE_PROJECT = 'cmr621_monitoring'
    SECRETS_DIR    = '/home/master/cmr621_monitoring/secrets'
    IMAGE          = 'cmr621/omd-labs-monitoring:1.0'
    ROLLBACK_IMAGE = 'cmr621/omd-labs-monitoring:rollback'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Verify agent') {
      steps {
        sh 'docker version'
        sh 'docker compose version'
        sh "test -d '${SECRETS_DIR}'"
        sh "test -f '${SECRETS_DIR}/omd_admin_password'"
        sh "test -f '${SECRETS_DIR}/snmp_community'"
      }
    }

    stage('Validate configuration') {
      steps {
        sh 'docker compose config -q'
        sh 'python3 -c "import sys, yaml; [yaml.safe_load(open(f, encoding=\'utf-8\')) for f in sys.argv[1:]]" bootstrap/playbook.yml bootstrap/inventory/devices.yml'
      }
    }

    stage('Keep rollback image') {
      steps {
        sh "docker image tag ${IMAGE} ${ROLLBACK_IMAGE} || true"
      }
    }

    stage('Build image') {
      steps {
        sh 'docker compose build'
      }
    }

    stage('Validate playbook') {
      steps {
        sh 'docker compose run --rm --no-deps --entrypoint ansible-playbook monitoring --syntax-check /root/ansible_dropin/playbook.yml'
      }
    }

    stage('Deploy') {
      when { branch 'main' }
      steps {
        sh "docker compose -p ${COMPOSE_PROJECT} up -d --force-recreate"
      }
    }

    stage('Smoke test') {
      when { branch 'main' }
      steps {
        sh "docker compose -p ${COMPOSE_PROJECT} ps"
        sh "docker compose -p ${COMPOSE_PROJECT} exec -T monitoring su - demo -c 'omd status'"
        sh "docker compose -p ${COMPOSE_PROJECT} exec -T monitoring su - demo -c 'naemon -v etc/naemon/naemon.cfg'"
        script {
          def code = sh(
            script: "docker compose -p ${COMPOSE_PROJECT} exec -T monitoring curl -sk -o /dev/null -w '%{http_code}' https://127.0.0.1/demo/",
            returnStdout: true
          ).trim()
          echo "Thruk HTTPS status: ${code}"
          if (code.isEmpty() || code == '000') {
            error('Thruk did not answer on the HTTPS endpoint')
          }
        }
      }
    }
  }

  post {
    failure {
      script {
        if (env.BRANCH_NAME == 'main') {
          sh "docker image tag ${ROLLBACK_IMAGE} ${IMAGE} || true"
          sh "docker compose -p ${COMPOSE_PROJECT} up -d --force-recreate || true"
        }
      }
    }
  }
}
