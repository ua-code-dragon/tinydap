# db-structure-migrator

In order to build Docker image, following command should be used

```
docker build -t db-structure .
```

After that, docker compose can be started using following command

```
docker-compose up -d
```

If **db-structure** service fails with not enough permissions to complete some action, please go modify the user role with superuser permissions 
