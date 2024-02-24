FROM containrrr/watchtower
RUN apk --no-cache add aws-cli
COPY ./watchtower/entry.sh /entry.sh
RUN chmod +x /entry.sh
ENTRYPOINT ["/entry.sh"]
CMD ["--help"]
