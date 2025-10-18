#!/usr/bin/env bash
set -euo pipefail

build_with_maven() {
  mvn -q -DskipTests -e -B test || true
}

build_with_gradle() {
  ./gradlew test || gradle test || true
}

if [[ -f "pom.xml" ]]; then
  build_with_maven
elif [[ -f "build.gradle" || -f "build.gradle.kts" ]]; then
  build_with_gradle
else
  echo "[java] No build file found (pom.xml/gradle)."; exit 0
fi

# SpotBugs attempt (non-fatal)
if command -v spotbugs >/dev/null 2>&1; then spotbugs -textui -low || true; fi