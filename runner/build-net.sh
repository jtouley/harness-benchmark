# Sourced (POSIX sh) by each RUN step of the runner images that downloads something.
#
# A host whose egress goes through a TLS-terminating proxy builds with the proxy's CA as a build secret:
#   docker build --network host --secret id=ca,src=CA.pem --build-arg HTTPS_PROXY ...
# (runner/pipeline/build.sh does this when HB_BUILD_CA is set). The secret is mounted only while the step
# runs, so the CA is in no layer. With it, this step's tools trust it: apt (over HTTPS, since the proxy
# refuses plain HTTP), curl, uv, pip and, when a JDK is present, Java (a truststore in /dev/shm, a tmpfs
# that no layer keeps). Without the secret nothing changes.
APT_OPTS=""
if [ -s /run/secrets/ca ]; then
  export SSL_CERT_FILE=/run/secrets/ca CURL_CA_BUNDLE=/run/secrets/ca REQUESTS_CA_BUNDLE=/run/secrets/ca \
    PIP_CERT=/run/secrets/ca NODE_EXTRA_CA_CERTS=/run/secrets/ca UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1
  APT_OPTS="-o Acquire::https::CAInfo=/run/secrets/ca"
  [ ! -f /etc/apt/sources.list.d/debian.sources ] ||
    sed -i 's#http://deb.debian.org#https://deb.debian.org#g' /etc/apt/sources.list.d/debian.sources
  if command -v keytool >/dev/null 2>&1 && [ ! -f /dev/shm/hb-ca.p12 ]; then
    awk '/BEGIN CERT/{n++} {print > ("/dev/shm/hb-ca-" n ".pem")}' /run/secrets/ca
    for pem in /dev/shm/hb-ca-*.pem; do
      keytool -importcert -noprompt -storetype PKCS12 -keystore /dev/shm/hb-ca.p12 -storepass changeit \
        -alias "$(basename "$pem" .pem)" -file "$pem" >/dev/null 2>&1 || true
    done
    rm -f /dev/shm/hb-ca-*.pem
  fi
  if [ -f /dev/shm/hb-ca.p12 ]; then
    proxy_hostport=${HTTPS_PROXY#http://}
    proxy_hostport=${proxy_hostport%/}
    JAVA_TOOL_OPTIONS="-Djavax.net.ssl.trustStore=/dev/shm/hb-ca.p12 -Djavax.net.ssl.trustStorePassword=changeit"
    JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS -Djavax.net.ssl.trustStoreType=PKCS12"
    [ -z "${HTTPS_PROXY:-}" ] || JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS -Dhttps.proxyHost=${proxy_hostport%:*} -Dhttps.proxyPort=${proxy_hostport##*:}"
    export JAVA_TOOL_OPTIONS
  fi
fi
