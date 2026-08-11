# Nautobot dependencies

Dedicated always-on PostgreSQL and Redis for the local scratch Nautobot.

`../.env` must define `NAUTOBOT_POSTGRES_DATA_DIR`. It may point at the
existing PostgreSQL data directory; keeping the machine-specific absolute path
in the ignored env file avoids embedding it in this Compose definition.

```sh
docker compose --env-file ../.env up -d
docker compose --env-file ../.env ps
```

The host ports remain 5432 and 6379 because the Nautobot containers use
`host.docker.internal`. Start this stack before `../nautobot/` on a cold boot.
