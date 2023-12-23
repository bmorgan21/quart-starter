# quart-starter

Before any of the commands will work, you MUST run `init` in each terminal.  After you run it, you will see that the terminal prompt is now prefixed with `(venv)`.  This is a visual confirmation that things are setup correctly.

# Helpful Links
* [Boostrap 5.3 Documentation](https://getbootstrap.com/docs/5.3)
* [Quart](https://quart.palletsprojects.com/en/latest/)
* [Tortoise ORM](https://tortoise.github.io/)

# Getting Started

To initialize the configuration files for Tortoise ORM you must run the following command.  This command only needs to be run if the migrations directory is removed in order to start over again.

`aerich init -t quart_starter.settings.TORTOISE_ORM`

In order to create an initial migration file, you can run the following command.  You should now see a file ending in `init.py` in `migrations/models` directory.

`aerich init-db`

At this point the database will be created and the schema will be applied.  You can connect to the DB with the following command:

`psql -h ${DB_HOST} -U ${DB_USER} ${DB_NAME}`

The password can be found in the `.devcontainer/docker-compose.yml` file.  One at the postgres prompt you can run `\dt` to see all the tables and then run `\d user` to see the user schema.

You can type `exit` or press `ctrl-d` to exit the postgres prompt.

When you are ready to extend your application and make changes to your models, you will need to also update the database schema.  This is managed through the same DB tool.  To create a new migration, you will run the following command with `XXX` replaced with a meaningful description (it is best to keep it short and to not have spaces):

`aerich migrate --name "XXX"`

This will create a new file in the migration/models directory.  At this point no changes have been made to the database.  In order to apply those changes you must run the following command:

`aerich upgrade`