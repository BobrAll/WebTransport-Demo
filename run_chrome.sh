#!/bin/bash
HASH=$(openssl x509 -pubkey -noout -in cert.pem | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64)

/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --origin-to-force-quic-on=127.0.0.1:4433 \
  --ignore-certificate-errors-spki-list=$HASH \
  https://127.0.0.1:4433
