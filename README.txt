#Connecting PostgreSQL: 

Create a Git Bash alias
Add this to your ~/.bashrc:
    `alias psql='/c/Program\ Files/PostgreSQL/18/bin/psql.exe'`
Reload:
    `source ~/.bashrc`
Then:
    `psql --version`
Running a script: 
    `psql -U postgres -d schema -f src/schema.sql`
run psql server
   `psql -U postgres -d schema`


   SET client_encoding TO 'UTF8';
SELECT * FROM works;


alias psql='/c/Program\ Files/PostgreSQL/18/bin/psql.exe'
source ~/.bashrc
psql --version

note: re run full fic link list from 1 - 882, fic status are inaccurate for those entries